"""
Government module extras: schemes that citizens can browse and apply to,
and officials manage.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_role

router = APIRouter(prefix="/gov", tags=["government"])


# ---------- Schemes ----------

@router.post("/schemes", response_model=schemas.SchemeOut)
def create_scheme(
    scheme_in: schemas.SchemeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    scheme = models.Scheme(created_by=current_user.id, **scheme_in.model_dump())
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.get("/schemes", response_model=List[schemas.SchemeOut])
def list_schemes(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Scheme)
    # Only officials can see deactivated schemes; everyone else sees active ones only
    if not (include_inactive and current_user.role == models.UserRole.official):
        query = query.filter(models.Scheme.is_active == True)
    return query.order_by(models.Scheme.created_at.desc()).all()


@router.patch("/schemes/{scheme_id}", response_model=schemas.SchemeOut)
def update_scheme(
    scheme_id: int,
    update_in: schemas.SchemeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    scheme = db.query(models.Scheme).filter(models.Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(scheme, field, value)

    db.commit()
    db.refresh(scheme)
    return scheme


@router.post("/schemes/{scheme_id}/apply", response_model=schemas.SchemeApplicationOut)
def apply_to_scheme(
    scheme_id: int,
    application_in: schemas.SchemeApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    scheme = db.query(models.Scheme).filter(models.Scheme.id == scheme_id).first()
    if not scheme or not scheme.is_active:
        raise HTTPException(status_code=404, detail="Scheme not found or no longer active")

    existing = (
        db.query(models.SchemeApplication)
        .filter(
            models.SchemeApplication.scheme_id == scheme_id,
            models.SchemeApplication.citizen_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You've already applied to this scheme")

    application = models.SchemeApplication(
        scheme_id=scheme_id,
        citizen_id=current_user.id,
        note=application_in.note,
        village=current_user.village,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/schemes/applications/mine", response_model=List[schemas.SchemeApplicationOut])
def my_scheme_applications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.SchemeApplication)
        .filter(models.SchemeApplication.citizen_id == current_user.id)
        .order_by(models.SchemeApplication.created_at.desc())
        .all()
    )


@router.get("/schemes/applications", response_model=List[schemas.SchemeApplicationOut])
def list_all_scheme_applications(
    scheme_id: Optional[int] = None,
    village: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    query = db.query(models.SchemeApplication)
    if scheme_id:
        query = query.filter(models.SchemeApplication.scheme_id == scheme_id)
    if village:
        query = query.filter(models.SchemeApplication.village.ilike(f"%{village}%"))
    return query.order_by(models.SchemeApplication.created_at.desc()).all()


@router.patch("/schemes/applications/{application_id}/status", response_model=schemas.SchemeApplicationOut)
def update_scheme_application_status(
    application_id: int,
    status_in: schemas.SchemeApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    application = db.query(models.SchemeApplication).filter(
        models.SchemeApplication.id == application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = status_in.status

    scheme = db.query(models.Scheme).filter(models.Scheme.id == application.scheme_id).first()
    db.add(models.Notification(
        user_id=application.citizen_id,
        message=f"Your application for '{scheme.title}' is now {status_in.status.value}",
    ))

    db.commit()
    db.refresh(application)
    return application

