from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.models import User, AuditLog

router = APIRouter(prefix='/api/audit', tags=['audit'])


@router.get('')
def get_audit_logs(
    _: User = Depends(require_roles('admin', 'auditor')),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    from_: datetime | None = Query(None, alias='from'),
    to_: datetime | None = Query(None, alias='to'),
):
    query = db.query(AuditLog, User).outerjoin(User, User.id == AuditLog.user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if from_:
        query = query.filter(AuditLog.created_at >= from_)
    if to_:
        query = query.filter(AuditLog.created_at <= to_)
    rows = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            'id': audit_log.id,
            'user_id': audit_log.user_id,
            'user': {'id': user.id, 'username': user.username, 'email': user.email} if user else None,
            'action': audit_log.action,
            'entity_type': audit_log.entity_type,
            'entity_id': audit_log.entity_id,
            'ip_address': audit_log.ip_address,
            'details': audit_log.details,
            'created_at': audit_log.created_at.isoformat(),
        }
        for audit_log, user in rows
    ]
