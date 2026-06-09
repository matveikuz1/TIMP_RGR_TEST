from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import AppException
from app.core.models import User
from app.core.schemas import ProfileUpdateRequest
from app.core.security import hash_password, verify_password

router = APIRouter(prefix='/api/users', tags=['users'])


from app.core.security import revoke_all_user_refresh_tokens

@router.put('/profile')
def update_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise AppException('INVALID_CREDENTIALS', 'Неверный текущий пароль', 400)

    if not payload.email and not payload.new_password:
        raise AppException('VALIDATION_ERROR', 'Нет данных для обновления', 400)

    if payload.email and payload.email != current_user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise AppException('VALIDATION_ERROR', 'Email уже используется', 400)
        current_user.email = payload.email

    if payload.new_password:
        current_user.password_hash = hash_password(payload.new_password)
        
        revoke_all_user_refresh_tokens(db, current_user.id)

    db.commit()
    db.refresh(current_user)
    return {'id': current_user.id, 'username': current_user.username, 'email': current_user.email, 'role': current_user.role}
