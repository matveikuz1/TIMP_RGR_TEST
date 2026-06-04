from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class APIError(BaseModel):
    error: bool = True
    code: str
    message: str
    error_id: str | None = None


def _validate_password_value(value: str) -> str:
    if len(value) < 8 or not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError('Пароль должен содержать минимум 8 символов, хотя бы одну букву и одну цифру')
    if any(c.isalpha() and not (('a' <= c <= 'z') or ('A' <= c <= 'Z')) for c in value):
        raise ValueError('Пароль должен содержать только латинские буквы')
    return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str):
        return _validate_password_value(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Verify2FARequest(BaseModel):
    email: EmailStr
    code: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_blocked: bool


class LinkCreateRequest(BaseModel):
    ttl_hours: int = Field(ge=1, le=24 * 30)
    max_uses: int = Field(ge=0, le=100, description='0 = unlimited uses')
    password: str | None = None


class LinkPasswordRequest(BaseModel):
    password: str | None = None


class ProfileUpdateRequest(BaseModel):
    email: EmailStr | None = None
    old_password: str
    new_password: str | None = None

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, value: str | None):
        if value is None:
            return value
        return _validate_password_value(value)


class FileOut(BaseModel):
    id: int
    owner_id: int
    original_name: str
    size_bytes: int
    mime_type: str
    sha256_hash: str
    uploaded_at: datetime


class LinkOut(BaseModel):
    id: int
    file_id: int
    token: str
    expires_at: datetime
    max_uses: int
    used_count: int
    revoked: bool


class AuditOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    ip_address: str | None
    details: dict | None
    created_at: datetime
