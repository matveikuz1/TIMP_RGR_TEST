from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.errors import AppException
from app.core.models import User, File

router = APIRouter(prefix='/api/admin', tags=['admin'])


def _user_to_dict(user: User):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_blocked': user.is_blocked,
        'created_at': user.created_at.isoformat(),
    }


def _file_to_dict(file_row: File):
    return {
        'id': file_row.id,
        'owner_id': file_row.owner_id,
        'original_name': file_row.original_name,
        'size_bytes': file_row.size_bytes,
        'mime_type': file_row.mime_type,
        'sha256_hash': file_row.sha256_hash,
        'uploaded_at': file_row.uploaded_at.isoformat(),
    }


@router.get('/users')
def list_users(
    _: User = Depends(require_roles('admin', 'auditor')),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    rows = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [_user_to_dict(user) for user in rows]


@router.get('/files')
def list_all_files(_: User = Depends(require_roles('admin', 'auditor')), db: Session = Depends(get_db)):
    return [_file_to_dict(file_row) for file_row in db.query(File).all()]


@router.post('/users/{user_id}/block')
def block_user(user_id: int, _: User = Depends(require_roles('admin')), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException('NOT_FOUND', 'Пользователь не найден', 404)
    user.is_blocked = True
    db.commit()
    return {'ok': True}


@router.post('/users/{user_id}/unblock')
def unblock_user(user_id: int, _: User = Depends(require_roles('admin')), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException('NOT_FOUND', 'Пользователь не найден', 404)
    user.is_blocked = False
    db.commit()
    return {'ok': True}
