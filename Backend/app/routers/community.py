"""
Module 1: Complaint creation, tracking, and the government dashboard.
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user, require_role
from ml.classifier import predict_department

router = APIRouter(prefix="/complaints", tags=["community"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "complaints")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB


def _complaint_out(complaint: models.Complaint) -> schemas.ComplaintOut:
    out = schemas.ComplaintOut.model_validate(complaint)
    if complaint.photo_path:
        out.photo_url = f"/uploads/complaints/{complaint.photo_path}"
    return out


@router.post("/", response_model=schemas.ComplaintOut)
def create_complaint(
    complaint_in: schemas.ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    department = predict_department(complaint_in.description)

    complaint = models.Complaint(
        citizen_id=current_user.id,
        title=complaint_in.title,
        description=complaint_in.description,
        location=complaint_in.location,
        priority=complaint_in.priority,
        department=department,
        village=current_user.village,  # tag the complaint with the citizen's village
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return _complaint_out(complaint)


@router.post("/{complaint_id}/photo", response_model=schemas.ComplaintOut)
def upload_complaint_photo(
    complaint_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your complaint")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP images are allowed")

    contents = file.file.read()
    if len(contents) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="Image must be under 5MB")

    filename = f"{complaint_id}_{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(contents)

    complaint.photo_path = filename
    db.commit()
    db.refresh(complaint)
    return _complaint_out(complaint)


@router.get("/mine", response_model=List[schemas.ComplaintOut])
def my_complaints(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    complaints = (
        db.query(models.Complaint)
        .filter(models.Complaint.citizen_id == current_user.id)
        .order_by(models.Complaint.created_at.desc())
        .all()
    )
    return [_complaint_out(c) for c in complaints]


@router.get("/{complaint_id}", response_model=schemas.ComplaintOut)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _complaint_out(complaint)


# ---- Comments (citizen who filed it, or any official) ----

def _check_comment_access(complaint: models.Complaint, user: models.User):
    if user.role != models.UserRole.official and complaint.citizen_id != user.id:
        raise HTTPException(status_code=403, detail="Not your complaint")


@router.get("/{complaint_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _check_comment_access(complaint, current_user)

    comments = (
        db.query(models.ComplaintComment)
        .filter(models.ComplaintComment.complaint_id == complaint_id)
        .order_by(models.ComplaintComment.created_at.asc())
        .all()
    )
    return [
        schemas.CommentOut(
            id=c.id,
            complaint_id=c.complaint_id,
            author_id=c.author_id,
            author_name=c.author.full_name,
            author_role=c.author.role,
            message=c.message,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.post("/{complaint_id}/comments", response_model=schemas.CommentOut)
def add_comment(
    complaint_id: int,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _check_comment_access(complaint, current_user)

    comment = models.ComplaintComment(
        complaint_id=complaint_id,
        author_id=current_user.id,
        message=comment_in.message,
    )
    db.add(comment)

    # Notify the citizen when an official replies
    if current_user.role == models.UserRole.official:
        db.add(models.Notification(
            user_id=complaint.citizen_id,
            message=f"An official replied on your complaint '{complaint.title}'",
            complaint_id=complaint_id,
        ))

    db.commit()
    db.refresh(comment)
    return schemas.CommentOut(
        id=comment.id,
        complaint_id=comment.complaint_id,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        author_role=current_user.role,
        message=comment.message,
        created_at=comment.created_at,
    )


# ---- Government dashboard (officials only) ----

@router.get("/", response_model=List[schemas.ComplaintOut])
def list_all_complaints(
    village: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    query = db.query(models.Complaint)
    if village:
        query = query.filter(models.Complaint.village.ilike(f"%{village}%"))
    complaints = query.order_by(models.Complaint.created_at.desc()).all()
    return [_complaint_out(c) for c in complaints]


@router.get("/villages/list", response_model=List[str])
def list_villages_with_complaints(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    rows = (
        db.query(models.Complaint.village)
        .filter(models.Complaint.village.isnot(None))
        .distinct()
        .all()
    )
    return sorted({r[0] for r in rows if r[0]})


@router.get("/villages/summary", response_model=List[schemas.VillageSummary])
def village_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    rows = (
        db.query(models.Complaint.village, func.count(models.Complaint.id))
        .filter(models.Complaint.village.isnot(None))
        .group_by(models.Complaint.village)
        .all()
    )
    return [
        {"village": v, "complaint_count": c}
        for v, c in sorted(rows, key=lambda r: r[0])
        if v
    ]


@router.patch("/{complaint_id}/status", response_model=schemas.ComplaintOut)
def update_complaint_status(
    complaint_id: int,
    status_in: schemas.ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.official)),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = status_in.status

    # Let the citizen know their complaint moved forward
    db.add(models.Notification(
        user_id=complaint.citizen_id,
        message=f"Your complaint '{complaint.title}' is now {status_in.status.value.replace('_', ' ')}",
        complaint_id=complaint.id,
    ))

    db.commit()
    db.refresh(complaint)
    return _complaint_out(complaint)


# ---- Notifications ----

@router.get("/notifications/mine", response_model=List[schemas.NotificationOut])
def my_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.patch("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}
