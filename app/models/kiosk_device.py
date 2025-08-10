import uuid
from sqlalchemy import Column, String, Boolean, Index, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.pg import Base

class KioskDevice(Base):
    __tablename__ = "kiosk_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Human-friendly label shown in admin
    name = Column(String(120), nullable=False)

    # Where the device is installed (Ward A, Lobby, 2F Wing B, etc.)
    location = Column(String(160))

    # Optional unique registration code/API key for device auth (add when you’re ready)
    # device_code = Column(String(64), unique=True, index=True)

    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    last_seen_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_kiosk_devices_name", name),
        Index("ix_kiosk_devices_is_active", is_active),
        Index("ix_kiosk_devices_last_seen_at", last_seen_at),
        Index("ix_kiosk_devices_created_at", created_at),
    )

    def __repr__(self) -> str:
        return f"<KioskDevice id={self.id} name={self.name!r} active={self.is_active}>"
