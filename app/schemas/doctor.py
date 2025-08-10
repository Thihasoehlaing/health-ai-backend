from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

class DoctorCreate(BaseModel):
    department_id: UUID
    name: str = Field(..., min_length=2, max_length=120)
    specialty: Optional[str] = None
    room: Optional[str] = None
    schedule_note: Optional[str] = None
    is_active: bool = True

class DoctorUpdate(BaseModel):
    department_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    specialty: Optional[str] = None
    room: Optional[str] = None
    schedule_note: Optional[str] = None
    is_active: Optional[bool] = None

class DoctorOut(BaseModel):
    id: UUID
    department_id: UUID
    name: str
    specialty: Optional[str] = None
    room: Optional[str] = None
    schedule_note: Optional[str] = None
    is_active: bool
    class Config:
        from_attributes = True
