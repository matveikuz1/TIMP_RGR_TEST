import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.core.models import ShareLink, File
from app.core.security import hash_password, verify_password


def _ensure_link_active(link: ShareLink) -> ShareLink:
    if link.revoked:
        raise AppException('LINK_REVOKED', 'Ссылка недействительна', 410)
    now = datetime.now(timezone.utc)
    expires_at = link.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise AppException('LINK_EXPIRED', 'Срок действия ссылки истек', 410)
    if link.max_uses > 0 and link.used_count >= link.max_uses:
        raise AppException('LINK_LIMIT_REACHED', 'Ссылка недействительна', 410)
    return link


def get_link_info(db: Session, token: str) -> tuple[ShareLink, File]:
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise AppException('NOT_FOUND', 'Ссылка недействительна', 404)
    _ensure_link_active(link)
    file_row = db.query(File).filter(File.id == link.file_id).first()
    if not file_row:
        raise AppException('NOT_FOUND', 'Файл не найден', 404)
    return link, file_row


def create_link(db: Session, file_row: File, owner_id: int, ttl_hours: int, max_uses: int, password: str | None):
    token = secrets.token_urlsafe(32)
    link = ShareLink(
        file_id=file_row.id,
        owner_id=owner_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        max_uses=max_uses,
        password_hash=hash_password(password) if password else None,
        revoked=False,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def validate_and_consume_link(db: Session, token: str, password: str | None) -> ShareLink:
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise AppException('NOT_FOUND', 'Ссылка недействительна', 404)
    _ensure_link_active(link)
    if link.password_hash and (not password or not verify_password(password, link.password_hash)):
        raise AppException('INVALID_LINK_PASSWORD', 'Неверный пароль ссылки', 401)

    link.used_count += 1
    db.commit()
    db.refresh(link)
    return link
