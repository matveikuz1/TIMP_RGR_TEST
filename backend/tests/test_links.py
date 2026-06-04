from datetime import datetime, timedelta, timezone
import secrets

import pytest

from app.core.database import SessionLocal
from app.core.errors import AppException
from app.core.models import User, File
from app.core.security import hash_password
from app.services.link_service import create_link, validate_and_consume_link


def _create_user_and_file():
    db = SessionLocal()
    suffix = secrets.token_hex(4)
    user = User(
        username=f'user_{suffix}',
        email=f'user_{suffix}@test.com',
        password_hash=hash_password('Password1'),
        role='user',
        is_blocked=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    file_row = File(
        owner_id=user.id,
        original_name='file.txt',
        stored_name=f'stored_{suffix}',
        size_bytes=12,
        mime_type='text/plain',
        sha256_hash=secrets.token_hex(32),
    )
    db.add(file_row)
    db.commit()
    db.refresh(file_row)
    return db, user, file_row


def test_link_token_generation():
    db, user, file_row = _create_user_and_file()
    try:
        link_one = create_link(db, file_row, user.id, ttl_hours=1, max_uses=1, password=None)
        link_two = create_link(db, file_row, user.id, ttl_hours=1, max_uses=1, password=None)
        assert link_one.token
        assert link_two.token
        assert link_one.token != link_two.token
    finally:
        db.close()


def test_link_expiration():
    db, user, file_row = _create_user_and_file()
    try:
        link = create_link(db, file_row, user.id, ttl_hours=1, max_uses=1, password=None)
        link.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        with pytest.raises(AppException) as exc_info:
            validate_and_consume_link(db, link.token, None)
        assert exc_info.value.code == 'LINK_EXPIRED'
    finally:
        db.close()


def test_link_usage_limit():
    db, user, file_row = _create_user_and_file()
    try:
        link = create_link(db, file_row, user.id, ttl_hours=1, max_uses=1, password=None)
        validate_and_consume_link(db, link.token, None)
        with pytest.raises(AppException) as exc_info:
            validate_and_consume_link(db, link.token, None)
        assert exc_info.value.code == 'LINK_LIMIT_REACHED'
    finally:
        db.close()
