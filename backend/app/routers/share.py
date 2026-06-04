from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppException
from app.core.schemas import LinkPasswordRequest
from app.core.security import verify_password
from app.services.link_service import get_link_info

router = APIRouter(prefix='/api/share', tags=['share'])


@router.post('/{token}/verify-password')
def verify_share_password(token: str, payload: LinkPasswordRequest, db: Session = Depends(get_db)):
    link, _ = get_link_info(db, token)
    if not link.password_hash:
        return {'ok': True, 'password_required': False}
    if not payload.password or not verify_password(payload.password, link.password_hash):
        raise AppException('INVALID_LINK_PASSWORD', 'Неверный пароль ссылки', 401)
    return {'ok': True, 'password_required': True}
