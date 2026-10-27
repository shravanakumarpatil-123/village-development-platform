# ─────────────────────────────────────────────────────────────────────────────
# ADD THESE TWO CLASSES TO THE BOTTOM OF backend/app/models.py
# ─────────────────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id              = Column(String, primary_key=True, default=gen_uuid)
    name            = Column(String, nullable=False)
    age             = Column(Integer, nullable=False)
    gender          = Column(String, nullable=False)
    phone           = Column(String, nullable=True)
    village         = Column(String, nullable=True)
    address         = Column(String, nullable=True)
    registered_by   = Column(String, ForeignKey("users.id"), nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    screenings = relationship("Screening", back_populates="patient")


class Screening(Base):
    __tablename__ = "screenings"

    id                  = Column(String, primary_key=True, default=gen_uuid)
    patient_id          = Column(String, ForeignKey("patients.id"), nullable=False)
    performed_by        = Column(String, ForeignKey("users.id"), nullable=True)
    photo_url           = Column(Text, nullable=True)

    # ML prediction results
    grade               = Column(Integer, nullable=True)
    grade_name          = Column(String, nullable=True)
    grade_description   = Column(Text, nullable=True)
    confidence          = Column(Float, nullable=True)
    confidence_percent  = Column(String, nullable=True)

    # Urgency (rule-based)
    urgency_level       = Column(String, nullable=True)
    urgency_label       = Column(String, nullable=True)
    urgency_color       = Column(String, nullable=True)
    action              = Column(Text, nullable=True)

    # AI advice
    advice              = Column(Text, nullable=True)
    disclaimer          = Column(Text, nullable=True)

    created_at          = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="screenings")
