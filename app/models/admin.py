import uuid
from sqlalchemy import Column, String, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.pg import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email: store as provided but enforce uniqueness case-insensitively via functional index below
    email = Column(String(254), nullable=False, index=True)        # 254 per RFC max
    password_hash = Column(String(255), nullable=False)            # bcrypt/argon2 fit
    role = Column(String(20), nullable=False, server_default="STAFF")  # SUPERADMIN | STAFF

    last_login_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    # Optional:
    # updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    __table_args__ = (
        # Case-insensitive unique email (functional unique index)
        Index("uq_admin_users_email_lower", text("lower(email)"), unique=True),
        Index("ix_admin_users_created_at", created_at),
        # Guard allowed roles without needing a DB enum
        CheckConstraint("role IN ('SUPERADMIN','STAFF')", name="ck_admin_users_role"),
    )

    def __repr__(self) -> str:
        return f"<AdminUser id={self.id} email={self.email!r} role={self.role}>"
