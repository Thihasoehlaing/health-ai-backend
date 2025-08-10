# app/routers/info.py
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.pg import get_db
from app.models.department import Department
from app.models.doctor import Doctor
from pydantic import BaseModel


router = APIRouter(prefix="/info", tags=["info"])


# --- Response models (lightweight) ---
class DepartmentPublic(BaseModel):
    id: UUID
    name: str
    floor: Optional[str] = None
    location: Optional[str] = None

class DoctorPublic(BaseModel):
    id: UUID
    name: str
    specialty: Optional[str] = None
    room: Optional[str] = None
    departmentId: UUID


@router.get("/departments", response_model=list[DepartmentPublic])
def list_departments(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search by department name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(Department).filter(Department.is_active.is_(True))
    if q:
        query = query.filter(func.lower(Department.name).like(f"%{q.lower()}%"))
    rows = (
        query.order_by(Department.name)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        DepartmentPublic(
            id=r.id, name=r.name, floor=r.floor, location=r.location_note
        )
        for r in rows
    ]


@router.get("/doctors", response_model=list[DoctorPublic])
def list_doctors(
    db: Session = Depends(get_db),
    departmentId: Optional[UUID] = Query(None, description="Filter by department UUID"),
    q: Optional[str] = Query(None, description="Search by doctor name or specialty"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(Doctor).filter(Doctor.is_active.is_(True))
    if departmentId:
        query = query.filter(Doctor.department_id == departmentId)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            func.lower(Doctor.name).like(like) | func.lower(Doctor.specialty).like(like)
        )
    rows = (
        query.order_by(Doctor.name)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        DoctorPublic(
            id=r.id,
            name=r.name,
            specialty=r.specialty,
            room=r.room,
            departmentId=r.department_id,
        )
        for r in rows
    ]
