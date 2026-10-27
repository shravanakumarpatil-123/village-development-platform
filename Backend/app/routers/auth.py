"""
Register, login, and "who am I" endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas
from app.security import hash_password, verify_password, create_access_token
from app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.phone:
        existing_phone = db.query(models.User).filter(models.User.phone == user_in.phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")

    # Only someone who knows the Gram Panchayat officer code can register as "official" —
    # this keeps the government dashboard limited to the one authorized officer.
    if user_in.role == models.UserRole.official:
        if user_in.official_code != settings.official_registration_code:
            raise HTTPException(status_code=403, detail="Invalid officer code")

    # ASHA worker verification: requires government ASHA registration number
    # and secret PHC (Primary Health Centre) authorization passcode to prevent misuse.
    if user_in.role == models.UserRole.asha_worker:
        if not user_in.asha_id or not user_in.asha_id.strip():
            raise HTTPException(status_code=400, detail="Government ASHA Worker Registration ID is required")
        if user_in.asha_code != settings.asha_registration_code:
            raise HTTPException(
                status_code=403,
                detail="Invalid PHC authorization code. Please enter the passcode provided by your Primary Health Centre."
            )
        existing_asha = db.query(models.User).filter(models.User.asha_id.ilike(user_in.asha_id.strip())).first()
        if existing_asha:
            raise HTTPException(status_code=400, detail="This ASHA Registration ID is already registered")

    user = models.User(
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        village=user_in.village,
        asha_id=user_in.asha_id.strip() if (user_in.asha_id and user_in.role == models.UserRole.asha_worker) else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm sends "username" — allows logging in with either email or phone number / personal ID
    identifier = form_data.username.strip()
    user = (
        db.query(models.User)
        .filter(
            (models.User.email.ilike(identifier))
            | (models.User.phone == identifier)
            | (models.User.asha_id.ilike(identifier))
        )
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email, phone, ASHA ID, or password")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user
