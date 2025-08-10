# Import all models here so they are registered with SQLAlchemy's Base.metadata
# and picked up by Alembic's autogenerate.


from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.faq import Faq
from app.models.admin import AdminUser
from app.models.kiosk_device import KioskDevice
from app.models.audit_log import AuditLog

__all__ = [
    "Department",
    "Doctor",
    "Patient",
    "Appointment",
    "Faq",
    "AdminUser",
    "KioskDevice",
    "AuditLog",
]