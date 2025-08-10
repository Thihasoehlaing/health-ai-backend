from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.pg import get_db
from app.security.deps import require_admin_token
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut

router = APIRouter(prefix="/admin/departments", tags=["admin-departments"])


@router.get("/", response_model=list[DepartmentOut], dependencies=[Depends(require_admin_token)])
def list_departments(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Search by name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Department)
    if q:
        query = query.filter(func.lower(Department.name).like(f"%{q.lower()}%"))
    rows = query.order_by(Department.name).limit(limit).offset(offset).all()
    return rows


@router.get("/{dep_id}", response_model=DepartmentOut, dependencies=[Depends(require_admin_token)])
def get_department(dep_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Department, dep_id)
    if not row:
        raise HTTPException(status_code=404, detail="Department not found")
    return row


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_token)])
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    # Soft unique check on name
    dup = db.query(Department).filter(func.lower(Department.name) == payload.name.lower()).first()
    if dup:
        raise HTTPException(status_code=409, detail="Department name already exists")

    row = Department(
        name=payload.name,
        floor=payload.floor,
        location_note=payload.location_note,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{dep_id}", response_model=DepartmentOut, dependencies=[Depends(require_admin_token)])
def update_department(dep_id: UUID, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    row = db.get(Department, dep_id)
    if not row:
        raise HTTPException(status_code=404, detail="Department not found")

    # If changing name, enforce uniqueness
    if payload.name and payload.name.lower() != (row.name or "").lower():
        dup = db.query(Department).filter(func.lower(Department.name) == payload.name.lower()).first()
        if dup and dup.id != dep_id:
            raise HTTPException(status_code=409, detail="Department name already exists")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_token)])
def delete_department(dep_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Department, dep_id)
    if not row:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(row)
    db.commit()
    return None
