"""
Defines what JSON shape comes IN to the API (what fields are required to
register, create a complaint, etc.) and what goes OUT (what the API returns).
Kept separate from models.py so we never accidentally expose things like
hashed_password in an API response.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models import (
    UserRole, ComplaintStatus, ComplaintPriority, ServiceRequestStatus, ProductRequestStatus,
    SchemeApplicationStatus, PatientGender,
)


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.citizen
    village: Optional[str] = None
    # Required only when role == official — the secret Gram Panchayat officer code.
    official_code: Optional[str] = None
    # Required only when role == asha_worker — Government ASHA registration number
    asha_id: Optional[str] = None
    # Required only when role == asha_worker — Primary Health Centre authorization code
    asha_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    village: Optional[str] = None
    asha_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Community complaints ----------

class ComplaintCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    priority: ComplaintPriority = ComplaintPriority.medium


class ComplaintOut(BaseModel):
    id: int
    citizen_id: int
    title: str
    description: str
    department: Optional[str]
    status: ComplaintStatus
    priority: ComplaintPriority
    location: Optional[str]
    village: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus


class VillageSummary(BaseModel):
    village: str
    complaint_count: int


class CommentCreate(BaseModel):
    message: str


class CommentOut(BaseModel):
    id: int
    complaint_id: int
    author_id: int
    author_name: str
    author_role: UserRole
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    message: str
    complaint_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Personal services ----------

class ProviderCreate(BaseModel):
    service_type: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProviderUpdate(BaseModel):
    service_type: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_available: Optional[bool] = None


class ProviderOut(BaseModel):
    id: int
    user_id: int
    service_type: str
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    is_available: bool
    average_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class ServiceRequestCreate(BaseModel):
    provider_id: int
    description: Optional[str] = None


class ServiceRequestStatusUpdate(BaseModel):
    status: ServiceRequestStatus


class ServiceRequestOut(BaseModel):
    id: int
    provider_id: int
    requester_id: int
    description: Optional[str]
    status: ServiceRequestStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    provider_id: int
    rating: int
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    provider_id: int
    reviewer_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Agriculture ----------

class ShopCreate(BaseModel):
    name: str
    location: Optional[str] = None


class ShopUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None


class ShopOut(BaseModel):
    id: int
    owner_id: int
    name: str
    location: Optional[str]

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0
    low_stock_threshold: int = 5


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None


class ProductOut(BaseModel):
    id: int
    shop_id: int
    name: str
    price: float
    stock: int
    low_stock_threshold: int = 5
    is_low_stock: bool = False

    class Config:
        from_attributes = True


class ProductRequestCreate(BaseModel):
    product_id: int
    quantity: int


class BatchRequestItem(BaseModel):
    product_id: int
    quantity: int


class BatchProductRequestCreate(BaseModel):
    items: List[BatchRequestItem]


class ProductRequestStatusUpdate(BaseModel):
    status: ProductRequestStatus


class ProductRequestOut(BaseModel):
    id: int
    product_id: int
    farmer_id: int
    quantity: int
    status: ProductRequestStatus
    batch_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Government module: Schemes ----------

class SchemeCreate(BaseModel):
    title: str
    description: str
    eligibility: Optional[str] = None
    department: Optional[str] = None


class SchemeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    eligibility: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class SchemeOut(BaseModel):
    id: int
    title: str
    description: str
    eligibility: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SchemeApplicationCreate(BaseModel):
    note: Optional[str] = None


class SchemeApplicationStatusUpdate(BaseModel):
    status: SchemeApplicationStatus


class SchemeApplicationOut(BaseModel):
    id: int
    scheme_id: int
    citizen_id: int
    note: Optional[str] = None
    status: SchemeApplicationStatus
    village: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Healthcare module: AppAyu V1 ----------

class PatientCreate(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[PatientGender] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None

    def get_full_name(self) -> str:
        return self.full_name or self.name or ""


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[PatientGender] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    asha_worker_id: Optional[int] = None
    full_name: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[PatientGender] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime

    def model_post_init(self, __context):
        if not self.name:
            self.name = self.full_name

    class Config:
        from_attributes = True


class MedicalHistoryCreate(BaseModel):
    condition: str
    notes: Optional[str] = None


class MedicalHistoryOut(BaseModel):
    id: int
    patient_id: int
    recorded_by_id: int
    condition: str
    notes: Optional[str] = None
    visit_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AIScreeningOut(BaseModel):
    id: int
    patient_id: int
    asha_worker_id: int
    screening_type: str
    image_url: Optional[str] = None
    model_version: Optional[str] = None
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
