from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta, date

# --- ensure "app" is importable when running this file directly ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.db.pg import SessionLocal
from app.models.admin import AdminUser
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus


def seed_postgres() -> None:
    db: Session = SessionLocal()
    try:
        # ---------- SUPERADMIN ----------
        admin_email = "admin@example.com"
        admin = db.query(AdminUser).filter(AdminUser.email == admin_email).first()
        if not admin:
            admin = AdminUser(
                email=admin_email,
                password_hash=bcrypt.hash("admin123"),
                role="SUPERADMIN",
            )
            db.add(admin)
            print(f"[+] SUPERADMIN created: {admin_email} / admin123")
        else:
            print(f"[-] SUPERADMIN exists: {admin_email}")

        # ---------- Department ----------
        dep_name = "Cardiology"
        dep = db.query(Department).filter(Department.name == dep_name).first()
        if not dep:
            dep = Department(name=dep_name, floor="2", location_note="Near elevator")
            db.add(dep)
            db.flush()  # ensure dep.id is available
            print(f"[+] Department created: {dep_name}")
        else:
            print(f"[-] Department exists: {dep_name}")

        # ---------- Doctor ----------
        doc_name = "Dr. Smith"
        doc = db.query(Doctor).filter(Doctor.name == doc_name).first()
        if not doc:
            # Use relationship so SQLAlchemy fills department_id correctly
            doc = Doctor(
                name=doc_name,
                specialty="Cardiologist",
                department=dep,  # <-- relationship avoids NULL FK
                room="201",
            )
            db.add(doc)
            print(f"[+] Doctor created: {doc_name}")
        else:
            print(f"[-] Doctor exists: {doc_name}")

        # ---------- Patient ----------
        mrn = "MRN123456"
        patient = db.query(Patient).filter(Patient.external_patient_id == mrn).first()
        if not patient:
            patient = Patient(
                full_name="John Doe",
                external_patient_id=mrn,
                dob=date(1980, 5, 20),  # DATE column; use date()
                phone="0123456789",
            )
            db.add(patient)
            print(f"[+] Patient created: {patient.full_name} ({mrn})")
        else:
            print(f"[-] Patient exists: {patient.full_name} ({mrn})")

        db.flush()  # ensure doc.id & patient.id are available

        # ---------- Appointment (tomorrow, 1h) ----------
        appt_exists = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.doctor_id == doc.id,
            )
            .first()
        )
        if not appt_exists:
            start = datetime.now() + timedelta(days=1)
            end = start + timedelta(hours=1)
            appt = Appointment(
                patient_id=patient.id,
                doctor_id=doc.id,
                start_time=start,
                end_time=end,
                status=AppointmentStatus.CONFIRMED,
                created_by_admin_id=admin.id,
            )
            db.add(appt)
            print(f"[+] Appointment created for {patient.full_name} with {doc.name}")
        else:
            print("[-] Sample appointment already exists")

        db.commit()
        print("[✓] Seeding completed!")
    except Exception as e:
        db.rollback()
        print(f"[x] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_postgres()
