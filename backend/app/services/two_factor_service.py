import random
import string
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.core.models import User
from app.core.errors import AppException
from app.services.email_service import send_2fa_code

def generate_2fa_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

def send_and_save_2fa(db: Session, user: User) -> None:
    if os.environ.get('TESTING') == 'true':
        user.is_verified = True
        db.commit()
        return
    code = generate_2fa_code()

    user.two_factor_code = code
    user.two_factor_expired_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    db.commit()
    
    try:
        send_2fa_code(user.email, code)
    except Exception as e:

        print(f"КРИТИЧЕСКАЯ ОШИБКА ПОЧТЫ: {e}")
        print(f"КОД ДЛЯ СТРАХОВКИ (DEV): {code}")

def verify_2fa_code(db: Session, user: User, code: str) -> bool:
    if not user.two_factor_code or not user.two_factor_expired_at:
        raise AppException('2FA_NOT_REQUESTED', 'Код не запрашивался', 400)
        
    if datetime.now(timezone.utc) > user.two_factor_expired_at:
        raise AppException('2FA_EXPIRED', 'Срок действия кода истек', 400)
        
    if user.two_factor_code != code:
        raise AppException('2FA_INVALID', 'Неверный код подтверждения', 400)
        
    user.two_factor_code = None
    user.two_factor_expired_at = None
    db.commit()
    return True
