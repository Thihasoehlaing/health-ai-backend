from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# -------- Requests --------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field("STAFF", pattern=r"^(SUPERADMIN|STAFF)$")


class AdminUpdateRole(BaseModel):
    role: str = Field(..., pattern=r"^(SUPERADMIN|STAFF)$")


# -------- Responses --------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminOut(BaseModel):
    id: UUID
    email: EmailStr
    role: str

    class Config:
        from_attributes = True  # Pydantic v2: allows ORM objects -> schema
