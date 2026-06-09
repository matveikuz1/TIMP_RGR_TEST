from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.models import RefreshToken
from app.core.config import settings
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)

def verify_refresh_token(db: Session, token: str):
    """Проверка refresh token в базе данных"""
    from app.core.models import RefreshToken
    from datetime import datetime, timezone
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()
    
    return refresh_token

def generate_refresh_token() -> str:
    """Генерирует случайный refresh token (не JWT, а случайная строка)"""
    return secrets.token_urlsafe(64)


def create_refresh_token(db: Session, user_id: int) -> RefreshToken:
    """Создаёт и сохраняет refresh token в БД"""
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    token_string = generate_refresh_token()
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_string,
        expires_at=expires_at,
        revoked=False
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def verify_refresh_token(db: Session, token: str) -> RefreshToken | None:
    """Проверяет refresh token: существует, не отозван, не истёк"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()
    return refresh_token


def revoke_refresh_token(db: Session, token: str) -> None:
    """Отзывает refresh token (при выходе или смене пароля)"""
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if refresh_token:
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.now(timezone.utc)
        db.commit()


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
    """Отзывает все refresh token пользователя (при смене пароля)"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({RefreshToken.revoked: True, RefreshToken.revoked_at: datetime.now(timezone.utc)})
    db.commit()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return str(payload.get('sub'))
    except JWTError:
        return None
