import uuid
from sqlalchemy import Column, String, Boolean, Text, Index, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.pg import Base

class Faq(Base):
    __tablename__ = "faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Map NLU intent -> canned answer
    intent_key = Column(String(120), nullable=False, unique=True)
    question   = Column(String(255), nullable=False)
    # If answers may be long, prefer Text. If short, you can switch back to String(1000) etc.
    answer     = Column(Text, nullable=False)

    is_active  = Column(Boolean, server_default=text("true"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_faqs_is_active", is_active),
        # You already get a unique index on intent_key from unique=True.
        # If you need case-insensitive uniqueness, remove unique=True above and use:
        # Index("uq_faqs_intent_key_lower", text("lower(intent_key)"), unique=True),
    )

    def __repr__(self) -> str:
        return f"<Faq id={self.id} intent_key={self.intent_key!r} active={self.is_active}>"
