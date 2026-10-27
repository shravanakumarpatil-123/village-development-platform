"""
Healthcare Module Router
=========================
Handles patient management, medical history, and AI-powered eye + skin screening.
"""

import os
import base64
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app import models, schemas
from app.ml.inference_eye import predict_eye_screening
from app.ml.inference_skin import predict_skin_condition

router = APIRouter(prefix="/healthcare", tags=["healthcare"])

HEALTHCARE_ROLES = (models.UserRole.official, models.UserRole.asha_worker)


# ---------- Patients ----------

@router.post("/patients", response_model=schemas.PatientOut, status_code=201)
def register_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    full_name = payload.get_full_name().strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="Patient name is required")

    patient = models.Patient(
        full_name=full_name,
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        village=payload.village,
        address=payload.address,
        asha_worker_id=current_user.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients", response_model=List[schemas.PatientOut])
def list_patients(
    village: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    query = db.query(models.Patient)
    if village:
        query = query.filter(models.Patient.village.ilike(f"%{village}%"))
    return query.order_by(models.Patient.created_at.desc()).all()


@router.get("/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: int,
    payload: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and data["full_name"]:
        patient.full_name = data["full_name"]
    elif "name" in data and data["name"]:
        patient.full_name = data["name"]

    for field in ("age", "gender", "phone", "village", "address"):
        if field in data:
            setattr(patient, field, data[field])

    db.commit()
    db.refresh(patient)
    return patient


# ---------- Medical History ----------

@router.post("/patients/{patient_id}/medical-history", response_model=schemas.MedicalHistoryOut, status_code=201)
def add_medical_history(
    patient_id: int,
    payload: schemas.MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    entry = models.MedicalHistoryEntry(
        patient_id=patient_id,
        recorded_by_id=current_user.id,
        condition=payload.condition,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/patients/{patient_id}/medical-history", response_model=List[schemas.MedicalHistoryOut])
def list_medical_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return (
        db.query(models.MedicalHistoryEntry)
        .filter(models.MedicalHistoryEntry.patient_id == patient_id)
        .order_by(models.MedicalHistoryEntry.visit_date.desc(), models.MedicalHistoryEntry.created_at.desc())
        .all()
    )


# ---------- AI Screenings ----------

@router.post("/patients/{patient_id}/screening", status_code=201)
@router.post("/patients/{patient_id}/screenings", status_code=201)
async def create_screening(
    patient_id: int,
    photo: Optional[UploadFile] = File(None, description="Image for screening (jpg/png)"),
    file: Optional[UploadFile] = File(None, description="Image for screening (jpg/png)"),
    screening_type: str = "eye",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    """
    Upload a photo and run AI screening.
    screening_type: 'eye' for diabetic retinopathy, 'skin' for skin conditions.
    """
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    upload = photo or file
    if not upload:
        raise HTTPException(status_code=400, detail="Image file is required")

    if upload.content_type and not upload.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    if screening_type not in ("eye", "skin"):
        raise HTTPException(status_code=400, detail="screening_type must be 'eye' or 'skin'")

    image_bytes = await upload.read()

    gender_str = (
        patient.gender.value
        if hasattr(patient.gender, "value")
        else (str(patient.gender) if patient.gender else None)
    )

    try:
        if screening_type == "eye":
            result = predict_eye_screening(
                image_bytes=image_bytes,
                patient_age=patient.age,
                patient_gender=gender_str,
            )
        else:
            result = predict_skin_condition(
                image_bytes=image_bytes,
                patient_age=patient.age,
                patient_gender=gender_str,
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e) + " Please train the model first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    # Save uploaded file
    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "screenings"
    )
    os.makedirs(upload_dir, exist_ok=True)
    orig_ext = upload.filename.split(".")[-1] if (upload.filename and "." in upload.filename) else "jpg"
    filename = f"screening_{patient_id}_{int(datetime.utcnow().timestamp())}.{orig_ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    prediction_text = (
        result.get("grade_name")
        or result.get("condition_display")
        or result.get("prediction")
        or ""
    )
    confidence_val = result.get("confidence")

    screening = models.AIScreening(
        patient_id=patient_id,
        asha_worker_id=current_user.id,
        screening_type=screening_type,
        image_path=f"/uploads/screenings/{filename}",
        prediction=prediction_text,
        confidence=confidence_val,
    )
    db.add(screening)
    db.commit()
    db.refresh(screening)

    return {
        "screening_id": screening.id,
        "patient_id": patient_id,
        "patient_name": patient.full_name,
        "screening_type": screening_type,
        **result,
    }


@router.get("/patients/{patient_id}/screenings")
def get_screening_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(*HEALTHCARE_ROLES)),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    screenings = (
        db.query(models.AIScreening)
        .filter(models.AIScreening.patient_id == patient_id)
        .order_by(models.AIScreening.created_at.desc())
        .all()
    )

    gender_str = (
        patient.gender.value
        if hasattr(patient.gender, "value")
        else (str(patient.gender) if patient.gender else None)
    )

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "name": patient.full_name,
            "age": patient.age,
            "gender": gender_str,
            "village": patient.village,
        },
        "screenings": [
            {
                "id": s.id,
                "screening_type": s.screening_type,
                "prediction": s.prediction,
                "confidence": s.confidence,
                "image_path": s.image_path,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in screenings
        ],
    }
