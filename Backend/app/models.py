"""
Defines the actual database tables as Python classes.
Each class here = one table in PostgreSQL. SQLAlchemy turns these into
'CREATE TABLE ...' statements when we call Base.metadata.create_all().
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    citizen = "citizen"
    official = "official"
    provider = "provider"
    farmer = "farmer"
    shop_owner = "shop_owner"
    asha_worker = "asha_worker"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.citizen)
    village = Column(String, nullable=True)  # which village under the Gram Panchayat
    asha_id = Column(String, unique=True, index=True, nullable=True)  # Official ASHA Registration ID
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="citizen")
    provider_profile = relationship("ServiceProvider", back_populates="user", uselist=False)
    shop = relationship("Shop", back_populates="owner", uselist=False)


# ---------- Module 1: Community complaints ----------

class ComplaintStatus(str, enum.Enum):
    submitted = "submitted"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class ComplaintPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String, nullable=True)  # filled in by the ML classifier
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.submitted)
    priority = Column(Enum(ComplaintPriority), default=ComplaintPriority.medium)
    location = Column(String, nullable=True)
    village = Column(String, nullable=True)  # copied from the citizen's profile at filing time
    photo_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = relationship("User", back_populates="complaints")
    comments = relationship("ComplaintComment", back_populates="complaint")


class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="comments")
    author = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- Module 2: Personal services ----------

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    service_type = Column(String, nullable=False)  # e.g. plumber, electrician
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)

    user = relationship("User", back_populates="provider_profile")
    requests = relationship("ServiceRequest", back_populates="provider")
    reviews = relationship("Review", back_populates="provider")


class ServiceRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    cancelled = "cancelled"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ServiceRequestStatus), default=ServiceRequestStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("ServiceProvider", back_populates="requests")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("ServiceProvider", back_populates="reviews")


# ---------- Module 3: Agriculture ----------

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    owner = relationship("User", back_populates="shop")
    products = relationship("Product", back_populates="shop")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True, default="Other agricultural input")
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)

    shop = relationship("Shop", back_populates="products")
    requests = relationship("ProductRequest", back_populates="product")


class ProductRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ProductRequest(Base):
    __tablename__ = "product_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(ProductRequestStatus), default=ProductRequestStatus.pending)
    batch_id = Column(String, nullable=True)  # groups multiple products requested together
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="requests")


# ---------- Government module: Schemes ----------

class SchemeApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    eligibility = Column(Text, nullable=True)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("SchemeApplication", back_populates="scheme")


class SchemeApplication(Base):
    __tablename__ = "scheme_applications"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)  # citizen's note when applying
    status = Column(Enum(SchemeApplicationStatus), default=SchemeApplicationStatus.pending)
    village = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="applications")


# ---------- Healthcare module: AppAyu V1 ----------
# ASHA workers register and manage patients, log medical history, and
# capture screening images. Screening predictions stay null until a real
# trained ML model is plugged into the inference step (see ml/ roadmap).

class PatientGender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    asha_worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # who registered them
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(Enum(PatientGender), nullable=True)
    phone = Column(String, nullable=True)
    village = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    medical_history = relationship("MedicalHistoryEntry", back_populates="patient")
    screenings = relationship("AIScreening", back_populates="patient")


class MedicalHistoryEntry(Base):
    __tablename__ = "medical_history_entries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition = Column(String, nullable=False)  # e.g. "Diabetes", "Fever - viral"
    notes = Column(Text, nullable=True)
    visit_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_history")


class AIScreening(Base):
    __tablename__ = "ai_screenings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    asha_worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    screening_type = Column(String, nullable=False, default="skin")  # skin | eye | oral (start with one)
    image_path = Column(String, nullable=False)
    model_version = Column(String, nullable=True)  # null until a real model is deployed
    prediction = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="screenings")
