# app/models/doctor.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, text, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.pg import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(120), nullable=False, index=True)
    specialty = Column(String(120))
    room = Column(String(50))
    schedule_note = Column(String(255))
    is_active = Column(Boolean, server_default=text("true"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    # If you later add Department.doctors back_populates, set this to match:
    # department = relationship("Department", back_populates="doctors", lazy="joined")
    department = relationship("Department", lazy="joined")

    __table_args__ = (
        # Common query patterns: active doctors in a department, sorted by name
        Index("ix_doctors_dept_active_name", department_id, is_active, name),
        Index("ix_doctors_created_at", created_at),
        # Optional uniqueness: prevent exact duplicates per department/room
        # Index("uq_doctors_dept_name_room", department_id, name, room, unique=True),
    )

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} name={self.name!r} dep={self.department_id}>"
