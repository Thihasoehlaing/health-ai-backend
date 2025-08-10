from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.pg import get_db
from app.security.deps import require_admin_token
from app.models.doctor import Doctor
from app.models.department import Department
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut

router = APIRouter(prefix="/admin/doctors", tags=["admin-doctors"])


@router.get("/", response_model=list[DoctorOut], dependencies=[Depends(require_admin_token)])
def list_doctors(
    db: Session = Depends(get_db),
    department_id: UUID | None = Query(None, description="Filter by department UUID"),
    q: str | None = Query(None, description="Search by name or specialty"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Doctor)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(func.lower(Doctor.name).like(like) | func.lower(Doctor.specialty).like(like))
    rows = query.order_by(Doctor.name).limit(limit).offset(offset).all()
    return rows


@router.get("/{doc_id}", response_model=DoctorOut, dependencies=[Depends(require_admin_token)])
def get_doctor(doc_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Doctor, doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return row


@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_token)])
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    # validate department
    if not db.get(Department, payload.department_id):
        raise HTTPException(status_code=400, detail="Invalid department_id")
    row = Doctor(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{doc_id}", response_model=DoctorOut, dependencies=[Depends(require_admin_token)])
def update_doctor(doc_id: UUID, payload: DoctorUpdate, db: Session = Depends(get_db)):
    row = db.get(Doctor, doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Doctor not found")
    # if moving to a new department, validate it exists
    if payload.department_id and not db.get(Department, payload.department_id):
        raise HTTPException(status_code=400, detail="Invalid department_id")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_token)])
def delete_doctor(doc_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Doctor, doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(row)
    db.commit()
    return None
