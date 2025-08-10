import uuid
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Enum as PgEnum,
    TIMESTAMP,
    text,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.pg import Base

class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time   = Column(TIMESTAMP(timezone=True), nullable=True)

    status = Column(
        PgEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        server_default=AppointmentStatus.PENDING.value,
        index=True,
    )

    created_by_admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    # Optional but useful:
    # updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    patient = relationship("Patient", lazy="joined")
    doctor  = relationship("Doctor", lazy="joined")

    __table_args__ = (
        # Ensure end_time is not before start_time
        CheckConstraint("(end_time IS NULL) OR (end_time >= start_time)", name="ck_appointment_time_order"),
        # Query patterns: list a doctor's upcoming appointments in order
        Index("ix_appt_doctor_start_time", "doctor_id", "start_time"),
        # Query patterns: list a patient's appointments by newest first
        Index("ix_appt_patient_start_time", "patient_id", "start_time"),
        # Helpful for dashboards/exports
        Index("ix_appt_created_at", "created_at"),
        # Optional: prevent exact duplicate slot for a doctor (soft guard)
        # Index("uq_appt_doctor_start", "doctor_id", "start_time", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} doctor={self.doctor_id} patient={self.patient_id} {self.start_time} status={self.status}>"
