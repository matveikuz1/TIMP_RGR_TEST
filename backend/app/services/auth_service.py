from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.core.models import User
from app.core.security import hash_password, verify_password


def register_user(db: Session, username: str, email: str, password: str) -> User:
    exists = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if exists:
        raise AppException('VALIDATION_ERROR', 'Пользователь с такими данными уже существует', 400)

    user = User(username=username, email=email, password_hash=hash_password(password), role='user', is_blocked=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise AppException('INVALID_CREDENTIALS', 'Неверный email или пароль', 401)
    if user.is_blocked:
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
    return user
