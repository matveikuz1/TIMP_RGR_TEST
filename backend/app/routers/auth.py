from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
from app.core.schemas import RegisterRequest, LoginRequest, Verify2FARequest
from app.core.security import create_access_token, create_refresh_token, revoke_all_user_refresh_tokens, revoke_refresh_token, verify_refresh_token
from app.core.errors import AppException
from app.services.audit_service import add_audit_log
from app.services.auth_service import register_user, authenticate_user
from app.services.two_factor_service import send_and_save_2fa, verify_2fa_code
from fastapi import APIRouter, Depends, Response, Request, status
from pydantic import BaseModel
router = APIRouter(prefix='/api/auth', tags=['auth'])

@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    send_and_save_2fa(db, user)
    db.commit()
    add_audit_log(db, user_id=user.id, action='REGISTER_PENDING_2FA', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    return {'requires_2fa': True, 'email': user.email, 'message': 'Код подтверждения отправлен на почту'}

@router.post('/verify-register')
def verify_register(payload: Verify2FARequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise AppException('USER_NOT_FOUND', 'Пользователь не найден', 404)

    verify_2fa_code(db, user, payload.code)

    user.is_verified = True
    db.commit()

    add_audit_log(db, user_id=user.id, action='CREATE_USER', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    return {'status': 'success', 'message': 'Аккаунт успешно подтвержден'}


@router.post('/login')
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except Exception:
        add_audit_log(db, user_id=None, action='LOGIN', entity_type='user', entity_id=None, ip_address=request.client.host if request.client else None, details={'status': 'failed'})
        raise

    send_and_save_2fa(db, user)
    db.commit()  # <--- ИСПРАВЛЕНИЕ: Фиксируем код для логина в БД!

    add_audit_log(db, user_id=user.id, action='LOGIN_PENDING_2FA', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    return {'requires_2fa': True, 'email': user.email}


@router.post('/verify-login')
def verify_login(payload: Verify2FARequest, response: Response, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise AppException('USER_NOT_FOUND', 'Пользователь не найден', 404)

    verify_2fa_code(db, user, payload.code)
    db.commit()

    # 1. Создаём access token (как и раньше)
    access_token = create_access_token(str(user.id))
    
    # 2. Создаём refresh token (НОВОЕ!)
    refresh_token = create_refresh_token(db, user.id)
    
    # 3. Устанавливаем access token в cookie
    response.set_cookie(
        key=settings.cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path='/',
    )
    
    # 4. Устанавливаем refresh token в отдельную cookie
    response.set_cookie(
        key=settings.refresh_token_name,
        value=refresh_token.token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path='/api/auth/refresh',  # 👈 Важно: только для эндпоинта обновления
    )
    
    add_audit_log(db, user_id=user.id, action='LOGIN', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    
    # Возвращаем данные пользователя (без токенов, они в cookie)
    return {'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role}

@router.post('/logout')
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    # 1. Удаляем access token cookie
    response.delete_cookie(settings.cookie_name)
    
    # 2. Удаляем refresh token cookie
    response.delete_cookie(settings.refresh_token_name)
    
    # 3. Отзываем refresh token в БД
    refresh_token_str = request.cookies.get(settings.refresh_token_name)
    if refresh_token_str:
        revoke_refresh_token(db, refresh_token_str)
    
    return {'ok': True}

@router.get('/me')
def get_me(current_user: User = Depends(get_current_user)):
    return {'id': current_user.id, 'username': current_user.username, 'email': current_user.email, 'role': current_user.role}

class RefreshTokenRequest(BaseModel):
    """Схема для запроса обновления токена (если передаём в теле, а не в cookie)"""
    refresh_token: str | None = None


@router.post('/refresh', status_code=status.HTTP_200_OK)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Обновление access token с помощью refresh token"""
    
    # 1. Берём refresh token из cookie (или из тела запроса)
    refresh_token_str = request.cookies.get(settings.refresh_token_name)
    
    # Альтернативный вариант: из тела запроса
    # body = request.json()
    # refresh_token_str = body.get('refresh_token')
    
    if not refresh_token_str:
        raise AppException('REFRESH_TOKEN_MISSING', 'Refresh token не найден', 401)
    
    # 2. Проверяем refresh token в БД
    refresh_token = verify_refresh_token(db, refresh_token_str)
    if not refresh_token:
        raise AppException('INVALID_REFRESH_TOKEN', 'Недействительный refresh token', 401)
    
    # 3. Получаем пользователя
    user = refresh_token.user
    if not user or user.is_blocked:
        raise AppException('USER_NOT_FOUND', 'Пользователь не найден или заблокирован', 401)
    
    # 4. Создаём НОВЫЙ access token
    new_access_token = create_access_token(str(user.id))
    
    # 5. (ОПЦИОНАЛЬНО) Создаём новый refresh token (токен-ротация)
    # Удаляем старый refresh token
    revoke_refresh_token(db, refresh_token_str)
    # Создаём новый
    new_refresh_token = create_refresh_token(db, user.id)
    response.set_cookie(
        key=settings.refresh_token_name,
        value=new_refresh_token.token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path='/api/auth/refresh',
    )
    
    # 6. Устанавливаем новый access token в cookie
    response.set_cookie(
        key=settings.cookie_name,
        value=new_access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path='/',
    )
    
    return {'ok': True, 'message': 'Токен обновлён'}
