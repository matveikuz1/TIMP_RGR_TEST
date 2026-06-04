import hashlib
import os
import secrets
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppException
from app.core.models import File, User, ShareLink


ALLOWED_MIME = {m.strip() for m in settings.allowed_mime_types.split(',') if m.strip()}
MAX_SIZE_BYTES = settings.max_file_size_mb * 1024 * 1024


def _ensure_upload_dir() -> Path:
    p = Path(settings.uploads_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_file(db: Session, owner: User, upload: UploadFile) -> File:
    if upload.content_type not in ALLOWED_MIME:
        raise AppException('UNSUPPORTED_MEDIA_TYPE', 'Тип файла не поддерживается', 415)

    content = upload.file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise AppException('FILE_TOO_LARGE', 'Файл превышает допустимый размер', 413)

    stored_name = secrets.token_hex(32)
    upload_dir = _ensure_upload_dir()
    path = upload_dir / stored_name

    with open(path, 'wb') as f:
        f.write(content)

    sha256_hash = hashlib.sha256(content).hexdigest()

    file_row = File(
        owner_id=owner.id,
        original_name=upload.filename or 'unknown',
        stored_name=stored_name,
        size_bytes=len(content),
        mime_type=upload.content_type,
        sha256_hash=sha256_hash,
    )
    db.add(file_row)
    db.commit()
    db.refresh(file_row)
    return file_row


def remove_file(db: Session, file_row: File):
    path = Path(settings.uploads_dir) / file_row.stored_name
    if path.exists():
        os.remove(path)
    db.query(ShareLink).filter(ShareLink.file_id == file_row.id).delete(synchronize_session=False)
    db.delete(file_row)
    db.commit()
