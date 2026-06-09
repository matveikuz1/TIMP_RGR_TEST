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

def _validate_username_value(value: str) -> str:
    if len(value) < 2 or len(value) > 64:
        raise ValueError('Имя пользователя должно содержать от 2 до 64 символов')
    if not all(c.isalnum() or c in '._-' for c in value):
        raise ValueError('Имя пользователя может содержать только буквы, цифры, точки, дефисы и подчёркивания')
    return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64, description='Имя пользователя (2-64 символа)')
    email: EmailStr = Field(description='Email адрес')
    password: str = Field(min_length=8, description='Пароль (минимум 8 символов)')

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str):
        return _validate_password_value(value)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str):
        return _validate_username_value(value)


class LoginRequest(BaseModel):
    email: EmailStr = Field(description='Email адрес')
    password: str = Field(description='Пароль')


class Verify2FARequest(BaseModel):
    email: EmailStr = Field(description='Email адрес')
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$', description='6-значный код подтверждения')


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_blocked: bool


class LinkCreateRequest(BaseModel):
    ttl_hours: int = Field(ge=1, le=24 * 30, description='Срок действия в часах (1-720)')
    max_uses: int = Field(ge=0, le=100, description='Максимум использований (0 = безлимит)')
    password: str | None = Field(None, min_length=4, max_length=100, description='Пароль для ссылки (опционально)')


class LinkPasswordRequest(BaseModel):
    password: str | None = Field(None, description='Пароль ссылки')


class ProfileUpdateRequest(BaseModel):
    email: EmailStr | None = Field(None, description='Новый email (опционально)')
    old_password: str = Field(description='Текущий пароль (обязательно для подтверждения)')
    new_password: str | None = Field(None, min_length=8, description='Новый пароль (опционально, минимум 8 символов)')

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, value: str | None):
        if value is None:
            return value
        return _validate_password_value(value)


class FileOut(BaseModel):
    id: int
    owner_id: int
    original_name: str = Field(max_length=255)
    size_bytes: int = Field(ge=0, le=100 * 1024 * 1024)
    mime_type: str = Field(max_length=128)
    sha256_hash: str = Field(min_length=64, max_length=64)
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
    action: str = Field(max_length=64)
    entity_type: str = Field(max_length=32)
    entity_id: str | None = Field(None, max_length=64)
    ip_address: str | None = Field(None, max_length=64)
    details: dict | None = None
    created_at: datetime
