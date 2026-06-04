from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.core.models import SystemEvent

ERROR_THRESHOLD_PER_HOUR = 10
ALERT_EVENT_TYPE = 'ADMIN_ALERT'


def _notify_admin(message: str):
    log_path = Path(__file__).resolve().parents[2] / 'logs' / 'monitoring.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now(timezone.utc).isoformat()} {message}\n')


def record_error(event_type: str, details: str):
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        db.add(SystemEvent(event_type=event_type, details=details))
        db.commit()
        since = now - timedelta(hours=1)
        error_count = (
            db.query(SystemEvent)
            .filter(SystemEvent.event_type == event_type, SystemEvent.created_at >= since)
            .count()
        )
        if error_count > ERROR_THRESHOLD_PER_HOUR:
            last_alert = (
                db.query(SystemEvent)
                .filter(SystemEvent.event_type == ALERT_EVENT_TYPE, SystemEvent.created_at >= since)
                .order_by(SystemEvent.created_at.desc())
                .first()
            )
            if not last_alert:
                alert_details = f'Ошибка: {error_count} за последний час'
                db.add(SystemEvent(event_type=ALERT_EVENT_TYPE, details=alert_details))
                db.commit()
                _notify_admin(f'ADMIN_ALERT {alert_details}')
    except SQLAlchemyError as exc:
        db.rollback()
        _notify_admin(f'ADMIN_ALERT мониторинг недоступен: {str(exc)[:200]}')
    finally:
        db.close()
