import uuid
from sqlalchemy import Column, String, Index, text
from sqlalchemy.dialects.postgresql import UUID, DATE, TIMESTAMP
from app.db.pg import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Hospital MRN / card number — typically unique
    external_patient_id = Column(String(120), index=True, unique=True)
    full_name = Column(String(160), nullable=False, index=True)
    dob = Column(DATE)
    phone = Column(String(32))            # keep short, store raw; format/validate in app layer
    note = Column(String(500))            # brief notes only; avoid PHI here
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_patients_created_at", created_at),
        # Optional: case-insensitive search on name (functional index)
        # Index("ix_patients_full_name_lower", text("lower(full_name)")),
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} ext_id={self.external_patient_id!r} name={self.full_name!r}>"
