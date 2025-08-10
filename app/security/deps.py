from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.pg import get_db
from app.models.admin import AdminUser

bearer = HTTPBearer()

def create_token(sub: str) -> str:
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def require_admin_token(token: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    try:
        payload = jwt.decode(token.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_admin(sub: str = Depends(require_admin_token), db: Session = Depends(get_db)) -> AdminUser:
    admin = db.get(AdminUser, UUID(sub))
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid token")
    return admin

def require_superadmin(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    if admin.role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="SUPERADMIN required")
    return admin
