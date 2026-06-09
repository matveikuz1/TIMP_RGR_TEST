from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppException
from app.core.models import User
from app.core.security import decode_token


# backend/app/core/deps.py
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.cookie_name)
    print(f"[DEBUG] get_current_user - token present: {bool(token)}")  # ✅ ДОБАВЬТЕ
    
    if not token:
        raise AppException('UNAUTHORIZED', 'Доступ запрещён', 401)
    user_id = decode_token(token)
    print(f"[DEBUG] get_current_user - user_id: {user_id}")  # ✅ ДОБАВЬТЕ
    
    if not user_id:
        raise AppException('UNAUTHORIZED', 'Доступ запрещён', 401)
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    # ⚠️ ПРОВЕРЬТЕ: не блокирует ли is_verified?
    print(f"[DEBUG] get_current_user - user found: {bool(user)}")
    print(f"[DEBUG] get_current_user - is_blocked: {user.is_blocked if user else None}")
    print(f"[DEBUG] get_current_user - is_verified: {user.is_verified if user else None}")  # ✅ ДОБАВЬТЕ
    
    # ⚠️ ВАЖНО: НЕ блокируем пользователя по is_verified для GET /me?
    if not user or user.is_blocked:
        raise AppException('UNAUTHORIZED', 'Доступ запрещён', 401)
    return user

def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
        return user

    return checker
