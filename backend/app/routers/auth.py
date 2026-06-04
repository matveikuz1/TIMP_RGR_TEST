from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.models import User
# ИСПРАВЛЕНО: Добавлен импорт Verify2FARequest
from app.core.schemas import RegisterRequest, LoginRequest, Verify2FARequest
from app.core.security import create_access_token
from app.core.errors import AppException # ИСПРАВЛЕНО: Добавлен импорт AppException
from app.services.audit_service import add_audit_log
from app.services.auth_service import register_user, authenticate_user
# ИСПРАВЛЕНО: Добавлен импорт функций 2FA
from app.services.two_factor_service import send_and_save_2fa, verify_2fa_code

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register')
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    send_and_save_2fa(db, user)
    # ИСПРАВЛЕНО: Исправлена опечатка dd_audit_log -> add_audit_log
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
    # ИСПРАВЛЕНО: Удален вызов verify_recaptcha, ломавший авторизацию
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except Exception:
        add_audit_log(db, user_id=None, action='LOGIN', entity_type='user', entity_id=None, ip_address=request.client.host if request.client else None, details={'status': 'failed'})
        raise

    send_and_save_2fa(db, user)
    
    add_audit_log(db, user_id=user.id, action='LOGIN_PENDING_2FA', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    return {'requires_2fa': True, 'email': user.email}


@router.post('/verify-login')
def verify_login(payload: Verify2FARequest, response: Response, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise AppException('USER_NOT_FOUND', 'Пользователь не найден', 404)
        
    verify_2fa_code(db, user, payload.code)
    
    token = create_access_token(str(user.id))
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
    )
    add_audit_log(db, user_id=user.id, action='LOGIN', entity_type='user', entity_id=str(user.id), ip_address=request.client.host if request.client else None, details={'status': 'success'})
    return {'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role}


@router.post('/logout')
def logout(response: Response):
    response.delete_cookie(settings.cookie_name)
    return {'ok': True}


@router.get('/me')
def get_me(current_user: User = Depends(get_current_user)):
    return {'id': current_user.id, 'username': current_user.username, 'email': current_user.email, 'role': current_user.role}
