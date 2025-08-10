import uuid
from sqlalchemy import Column, String, Boolean, text, Index, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.pg import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Set a sensible max length for better indexing / validation
    name = Column(String(120), nullable=False, unique=True)
    floor = Column(String(20))            # keep short (e.g., "2", "GF", "L3")
    location_note = Column(String(255))   # brief notes; long text not needed
    is_active = Column(Boolean, server_default=text("true"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    # Optional: track edits
    # updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    __table_args__ = (
        # Helpful indexes
        Index("ix_departments_name", name),
        Index("ix_departments_is_active", is_active),
        Index("ix_departments_created_at", created_at),
        # Optional: case-insensitive unique name (Postgres functional index).
        # If you want this, remove `unique=True` above and use this instead:
        # Index("uq_departments_name_lower", func.lower(name), unique=True),
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r}>"
