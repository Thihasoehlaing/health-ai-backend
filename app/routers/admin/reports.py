# app/routers/admin/reports.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.security.deps import require_admin_token
from app.db.pg import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])


@router.get("/usage", dependencies=[Depends(require_admin_token)])
def usage_report(db: Session = Depends(get_db)):
    """Return a simple usage summary for the last 30 days."""
    today = date.today()
    start_date = today - timedelta(days=30)

    total_patients = db.query(func.count(Patient.id)).scalar()
    total_doctors = db.query(func.count(Doctor.id)).scalar()

    appt_counts = (
        db.query(
            Appointment.status,
            func.count(Appointment.id).label("count")
        )
        .filter(Appointment.start_time >= start_date)
        .group_by(Appointment.status)
        .all()
    )

    # Convert to dict like {"PENDING": 10, "CONFIRMED": 5, ...}
    appt_summary = {status: count for status, count in appt_counts}

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "appointments_last_30_days": appt_summary,
    }
