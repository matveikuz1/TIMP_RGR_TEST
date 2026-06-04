from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.models import AuditLog, SystemEvent


def add_audit_log(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    ip_address: str | None,
    details: dict | None = None,
):
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            details=details,
        )
        db.add(entry)
        db.commit()
    except OperationalError:
        db.rollback()
        log_path = Path(__file__).resolve().parents[2] / 'logs' / 'system_events.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write('DB_UNAVAILABLE while writing audit_log\n')


def add_system_event(db: Session, event_type: str, details: str):
    event = SystemEvent(event_type=event_type, details=details)
    db.add(event)
    db.commit()
