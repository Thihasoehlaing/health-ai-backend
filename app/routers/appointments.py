from __future__ import annotations

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.db.pg import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.appointment import (
    AppointmentCheckRequest,
    AppointmentCheckResponse,
    AppointmentItem,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _try_parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(value)
    except Exception:
        return None


@router.post("/check", response_model=AppointmentCheckResponse)
def check_appointments(
    payload: AppointmentCheckRequest,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    upcoming_only: bool = Query(False, description="If true, only future appointments are returned"),
):
    term = (payload.patientIdOrName or "").strip()
    if not term:
        return AppointmentCheckResponse(items=[])

    # Base query
    q = (
        db.query(Appointment, Patient, Doctor)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Doctor, Doctor.id == Appointment.doctor_id)
    )

    # Filters: UUID (Patient.id), exact external_patient_id, or ilike on full_name
    as_uuid = _try_parse_uuid(term)
    if as_uuid:
        q = q.filter(Patient.id == as_uuid)
    else:
        q = q.filter(
            or_(
                Patient.external_patient_id == term,
                func.lower(Patient.full_name).like(f"%{term.lower()}%"),
            )
        )

    if upcoming_only:
        now = datetime.now(timezone.utc)
        q = q.filter(Appointment.start_time >= now)

    rows = (
        q.order_by(Appointment.start_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items: list[AppointmentItem] = [
        AppointmentItem(
            id=a.id,
            doctorName=d.name,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status,
        )
        for (a, p, d) in rows
    ]
    return AppointmentCheckResponse(items=items)


@router.get("/{appointment_id}", response_model=AppointmentItem)
def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
):
    row = (
        db.query(Appointment, Doctor)
        .join(Doctor, Doctor.id == Appointment.doctor_id)
        .filter(Appointment.id == appointment_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")

    a, d = row
    return AppointmentItem(
        id=a.id,
        doctorName=d.name,
        start_time=a.start_time,
        end_time=a.end_time,
        status=a.status,
    )
