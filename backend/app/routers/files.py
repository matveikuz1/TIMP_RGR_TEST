from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File as UploadField, Request, Query, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import AppException
from app.core.models import File, User, ShareLink
from app.core.schemas import LinkCreateRequest
from app.services.audit_service import add_audit_log
from app.services.file_service import save_file, remove_file
from app.services.link_service import create_link, get_link_info, validate_and_consume_link
router = APIRouter(prefix='/api/files', tags=['files'])
public_router = APIRouter(prefix='/api/share', tags=['share'])
links_router = APIRouter(prefix='/api/links', tags=['links'])


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


def _link_to_dict(link: ShareLink):
    return {
        'id': link.id,
        'file_id': link.file_id,
        'owner_id': link.owner_id,
        'token': link.token,
        'expires_at': link.expires_at.isoformat(),
        'max_uses': link.max_uses,
        'used_count': link.used_count,
        'revoked': link.revoked,
    }


@router.get('')
def list_my_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    raise Exception("Тестовая внутренняя ошибка сервера")
    rows = (
        db.query(File)
        .filter(File.owner_id == current_user.id)
        .order_by(File.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_file_to_dict(row) for row in rows]

@router.post('/upload', status_code=status.HTTP_201_CREATED)
def upload_file(upload: UploadFile = UploadField(...), request: Request = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_row = save_file(db, current_user, upload)
    add_audit_log(db, user_id=current_user.id, action='UPLOAD_FILE', entity_type='file', entity_id=str(file_row.id), ip_address=request.client.host if request and request.client else None)
    return _file_to_dict(file_row)

@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: int, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_row = db.query(File).filter(File.id == file_id).first()
    if not file_row:
        raise AppException('NOT_FOUND', 'Файл не найден', 404)
    if current_user.role != 'admin' and file_row.owner_id != current_user.id:
        add_audit_log(db, user_id=current_user.id, action='ACCESS_DENIED', entity_type='file', entity_id=str(file_id), ip_address=request.client.host if request.client else None)
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)

    remove_file(db, file_row)
    add_audit_log(db, user_id=current_user.id, action='DELETE_FILE', entity_type='file', entity_id=str(file_id), ip_address=request.client.host if request.client else None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post('/{file_id}/links', status_code=status.HTTP_201_CREATED)
def create_file_link(file_id: int, payload: LinkCreateRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_row = db.query(File).filter(File.id == file_id).first()
    if not file_row:
        raise AppException('NOT_FOUND', 'Файл не найден', 404)
    if current_user.role != 'admin' and file_row.owner_id != current_user.id:
        add_audit_log(db, user_id=current_user.id, action='ACCESS_DENIED', entity_type='file', entity_id=str(file_id), ip_address=request.client.host if request.client else None)
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)

    link = create_link(db, file_row, current_user.id, payload.ttl_hours, payload.max_uses, payload.password)
    add_audit_log(db, user_id=current_user.id, action='CREATE_LINK', entity_type='link', entity_id=str(link.id), ip_address=request.client.host if request.client else None)
    return {'id': link.id, 'token': link.token, 'url': f'/share/{link.token}'}

@router.get('/{file_id}/links')
def list_file_links(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_row = db.query(File).filter(File.id == file_id).first()
    if not file_row:
        raise AppException('NOT_FOUND', 'Файл не найден', 404)
    if current_user.role != 'admin' and file_row.owner_id != current_user.id:
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
    rows = db.query(ShareLink).filter(ShareLink.file_id == file_id).all()
    return [_link_to_dict(row) for row in rows]


@router.delete('/links/{link_id}', status_code=status.HTTP_204_NO_CONTENT)
def revoke_link(link_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.id == link_id).first()
    if not link:
        raise AppException('NOT_FOUND', 'Ссылка не найдена', 404)
    if current_user.role != 'admin' and link.owner_id != current_user.id:
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
    link.revoked = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

def _download_shared_file(token: str, password: str | None, request: Request | None, db: Session) -> FileResponse:
    link = validate_and_consume_link(db, token, password)
    file_row = db.query(File).filter(File.id == link.file_id).first()
    
    if not file_row:
        raise AppException('NOT_FOUND', 'Файл не найден', 404)
    
    path = Path(settings.uploads_dir) / file_row.stored_name
    if not path.exists():
        raise AppException('NOT_FOUND', 'Файл не найден', 404)

    add_audit_log(db, user_id=None, action='DOWNLOAD_FILE', entity_type='file', entity_id=str(file_row.id), ip_address=request.client.host if request and request.client else None, details={'link_id': link.id})
    return FileResponse(path=str(path), media_type=file_row.mime_type, filename=file_row.original_name)

@router.get('/download/{token}')
def download_by_token(token: str, password: str | None = None, request: Request = None, db: Session = Depends(get_db)):
    return _download_shared_file(token, password, request, db)

@public_router.get('/{token}')
def get_share_info(token: str, db: Session = Depends(get_db)):
    link, file_row = get_link_info(db, token)
    owner = db.query(User).filter(User.id == link.owner_id).first()
    return {
        'file': _file_to_dict(file_row),
        'link': _link_to_dict(link),
        'owner': {'id': owner.id, 'username': owner.username, 'email': owner.email} if owner else None,
        'password_required': bool(link.password_hash),
    }

@public_router.get('/{token}/download')
def download_by_share_token(token: str, password: str | None = None, request: Request = None, db: Session = Depends(get_db)):
    return _download_shared_file(token, password, request, db)


@links_router.get('')
def list_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(ShareLink)
    if current_user.role not in ('admin', 'auditor'):
        query = query.filter(ShareLink.owner_id == current_user.id)
    rows = query.order_by(ShareLink.created_at.desc()).offset(offset).limit(limit).all()
    return [_link_to_dict(row) for row in rows]

@router.delete('/links/{link_id}/permanent', status_code=status.HTTP_204_NO_CONTENT)
def permanent_delete_link(link_id: int, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.id == link_id).first()
    if not link:
        raise AppException('NOT_FOUND', 'Ссылка не найдена', 404)
    if current_user.role != 'admin' and link.owner_id != current_user.id:
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
    
    db.delete(link)
    db.commit()
    
    add_audit_log(db, user_id=current_user.id, action='DELETE_LINK', entity_type='link', entity_id=str(link_id), ip_address=request.client.host if request.client else None, details={'permanent': True})
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post('/links/{link_id}/restore', status_code=status.HTTP_200_OK)
def restore_link(link_id: int, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.id == link_id).first()
    if not link:
        raise AppException('NOT_FOUND', 'Ссылка не найдена', 404)
    if current_user.role != 'admin' and link.owner_id != current_user.id:
        raise AppException('ACCESS_DENIED', 'Доступ запрещён', 403)
    
    link.revoked = False
    db.commit()
    
    add_audit_log(db, user_id=current_user.id, action='RESTORE_LINK', entity_type='link', entity_id=str(link_id), ip_address=request.client.host if request.client else None)
    return {'ok': True, 'message': 'Ссылка восстановлена'}
