# app/models/audit_log.py
import uuid
from sqlalchemy import Column, String, ForeignKey, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from app.db.pg import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who did it: ADMIN | SYSTEM
    actor_type = Column(String(16), nullable=False)  # small, controlled values
    actor_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)

    # What happened
    action = Column(String(120), nullable=False)     # e.g., CREATE_DOCTOR, UPDATE_APPOINTMENT
    meta_json = Column(JSONB)                        # structured details for the action

    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_audit_logs_actor_type", actor_type),
        Index("ix_audit_logs_created_at", created_at),
        CheckConstraint("actor_type IN ('ADMIN','SYSTEM')", name="ck_audit_logs_actor_type"),
        # If you plan to query meta_json frequently (e.g., meta_json->>'doctor_id'):
        # Index("ix_audit_logs_meta_json", meta_json, postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} actor={self.actor_type}:{self.actor_id} action={self.action!r}>"
