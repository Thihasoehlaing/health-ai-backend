from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    floor: Optional[str] = None
    location_note: Optional[str] = None
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    floor: Optional[str] = None
    location_note: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentOut(BaseModel):
    id: UUID
    name: str
    floor: Optional[str] = None
    location_note: Optional[str] = None
    is_active: bool
    class Config:
        from_attributes = True
