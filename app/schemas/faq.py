from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

class FaqCreate(BaseModel):
    intent_key: str = Field(..., min_length=2, max_length=120)
    question: str
    answer: str
    is_active: bool = True

class FaqUpdate(BaseModel):
    intent_key: Optional[str] = Field(None, min_length=2, max_length=120)
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None

class FaqOut(BaseModel):
    id: UUID
    intent_key: str
    question: str
    answer: str
    is_active: bool
    class Config:
        from_attributes = True
