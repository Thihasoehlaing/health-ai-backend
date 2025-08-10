from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.hash import bcrypt

from app.db.pg import get_db
from app.models.admin import AdminUser
from app.security.deps import create_token, get_current_admin, require_superadmin
from app.schemas.auth import (
    LoginRequest, TokenResponse,
    AdminCreate, AdminOut, ChangePasswordRequest, AdminUpdateRole
)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


# --- LOGIN ---
@router.post("/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    admin = db.query(AdminUser).filter(func.lower(AdminUser.email) == email).first()
    if not admin or not bcrypt.verify(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(str(admin.id))
    # Optionally update last_login_at:
    # from sqlalchemy import text
    # admin.last_login_at = text("now()"); db.commit()
    return TokenResponse(access_token=token)


# --- WHO AM I ---
@router.get("/me", response_model=AdminOut)
def me(current: AdminUser = Depends(get_current_admin)):
    return current


# --- CHANGE PASSWORD (self) ---
@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not bcrypt.verify(payload.old_password, current.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    if payload.old_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")
    current.password_hash = bcrypt.hash(payload.new_password)
    db.commit()
    return None


# --- CREATE ADMIN (SUPERADMIN only) ---
@router.post("/admins", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    _: AdminUser = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    dup = db.query(AdminUser).filter(func.lower(AdminUser.email) == email).first()
    if dup:
        raise HTTPException(status_code=409, detail="Email already exists")
    row = AdminUser(email=email, password_hash=bcrypt.hash(payload.password), role=payload.role)
    db.add(row); db.commit(); db.refresh(row)
    return row


# --- LIST ADMINS (SUPERADMIN only) ---
@router.get("/admins", response_model=List[AdminOut])
def list_admins(
    q: str | None = Query(None, description="Search by email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: AdminUser = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    query = db.query(AdminUser)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(func.lower(AdminUser.email).like(like))
    rows = query.order_by(AdminUser.created_at.desc()).limit(limit).offset(offset).all()
    return rows


# --- UPDATE ADMIN ROLE (SUPERADMIN only) ---
@router.patch("/admins/{admin_id}/role", response_model=AdminOut)
def update_admin_role(
    admin_id: UUID,
    payload: AdminUpdateRole,
    _: AdminUser = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    row = db.get(AdminUser, admin_id)
    if not row:
        raise HTTPException(status_code=404, detail="Admin not found")
    row.role = payload.role
    db.commit(); db.refresh(row)
    return row


# --- DELETE ADMIN (SUPERADMIN only) ---
@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: UUID,
    _: AdminUser = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    row = db.get(AdminUser, admin_id)
    if not row:
        raise HTTPException(status_code=404, detail="Admin not found")
    db.delete(row)
    db.commit()
    return None
