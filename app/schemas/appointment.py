# app/schemas/appointments.py
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentCheckRequest(BaseModel):
    patientIdOrName: str = Field(..., min_length=1, description="UUID or full/partial patient name")


class AppointmentItem(BaseModel):
    id: UUID
    doctorName: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str

    class Config:
        orm_mode = True  # allows returning SQLAlchemy objects directly


class AppointmentCheckResponse(BaseModel):
    items: list[AppointmentItem]
