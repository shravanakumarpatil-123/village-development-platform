"""
Module 2: Provider profiles, nearby search, service requests, reviews.
"""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/services", tags=["personal"])


def _distance_km(lat1, lon1, lat2, lon2) -> float:
    """Straight-line distance between two lat/lon points, in kilometers."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@router.post("/providers", response_model=schemas.ProviderOut)
def create_provider_profile(
    provider_in: schemas.ProviderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = (
        db.query(models.ServiceProvider)
        .filter(models.ServiceProvider.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Provider profile already exists")

    provider = models.ServiceProvider(user_id=current_user.id, **provider_in.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/providers/mine", response_model=schemas.ProviderOut)
def get_my_provider_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    provider = (
        db.query(models.ServiceProvider)
        .filter(models.ServiceProvider.user_id == current_user.id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="You don't have a provider profile yet")
    return provider


@router.patch("/providers/mine", response_model=schemas.ProviderOut)
def update_my_provider_profile(
    update_in: schemas.ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    provider = (
        db.query(models.ServiceProvider)
        .filter(models.ServiceProvider.user_id == current_user.id)
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="You don't have a provider profile yet")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)

    db.commit()
    db.refresh(provider)
    return provider


@router.get("/providers", response_model=List[schemas.ProviderOut])
def search_providers(
    service_type: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 10,
    db: Session = Depends(get_db),
):
    query = db.query(models.ServiceProvider).filter(models.ServiceProvider.is_available == True)
    if service_type:
        query = query.filter(models.ServiceProvider.service_type.ilike(f"%{service_type}%"))
    providers = query.all()

    if latitude is not None and longitude is not None:
        providers = [
            p for p in providers
            if p.latitude is not None and p.longitude is not None
            and _distance_km(latitude, longitude, p.latitude, p.longitude) <= radius_km
        ]

    results = []
    for p in providers:
        reviews = db.query(models.Review).filter(models.Review.provider_id == p.id).all()
        out = schemas.ProviderOut.model_validate(p)
        out.review_count = len(reviews)
        out.average_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
        results.append(out)
    return results


@router.post("/requests", response_model=schemas.ServiceRequestOut)
def create_service_request(
    request_in: schemas.ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    provider = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.id == request_in.provider_id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    req = models.ServiceRequest(
        provider_id=request_in.provider_id,
        requester_id=current_user.id,
        description=request_in.description,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/requests/mine", response_model=List[schemas.ServiceRequestOut])
def my_service_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ServiceRequest)
        .filter(models.ServiceRequest.requester_id == current_user.id)
        .order_by(models.ServiceRequest.created_at.desc())
        .all()
    )


@router.get("/requests/incoming", response_model=List[schemas.ServiceRequestOut])
def incoming_requests_for_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    provider = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.user_id == current_user.id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="You don't have a provider profile yet")

    return (
        db.query(models.ServiceRequest)
        .filter(models.ServiceRequest.provider_id == provider.id)
        .order_by(models.ServiceRequest.created_at.desc())
        .all()
    )


@router.patch("/requests/{request_id}/status", response_model=schemas.ServiceRequestOut)
def update_service_request_status(
    request_id: int,
    status_in: schemas.ServiceRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    provider = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.id == req.provider_id
    ).first()
    if provider.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your request to update")

    req.status = status_in.status
    db.commit()
    db.refresh(req)
    return req


@router.post("/reviews", response_model=schemas.ReviewOut)
def create_review(
    review_in: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not (1 <= review_in.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    provider = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.id == review_in.provider_id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    review = models.Review(
        provider_id=review_in.provider_id,
        reviewer_id=current_user.id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/providers/{provider_id}/reviews", response_model=List[schemas.ReviewOut])
def list_provider_reviews(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(models.ServiceProvider).filter(
        models.ServiceProvider.id == provider_id
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return (
        db.query(models.Review)
        .filter(models.Review.provider_id == provider_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
