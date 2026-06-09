from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.core.models import SystemEvent
from app.core.config import settings

ERROR_THRESHOLD_PER_HOUR = 10
ALERT_EVENT_TYPE = 'ADMIN_ALERT'

_last_notification_time = {}


def _get_last_notification_time(error_type: str):
    return _last_notification_time.get(error_type)


def _set_last_notification_time(error_type: str, time):
    _last_notification_time[error_type] = time


def _get_recent_errors_from_file(error_type: str, hours: int = 1, limit: int = 15) -> list:
    """Получение последних ошибок из файлового лога"""
    log_path = Path(__file__).resolve().parents[2] / 'logs' / 'monitoring.log'
    if not log_path.exists():
        return []
    
    errors = []
    cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines):
                if len(errors) >= limit:
                    break
                if error_type in line or 'ERROR' in line or 'ADMIN_ALERT' in line:
                    try:
                        time_str = line.split(' ')[0]
                        line_time = datetime.fromisoformat(time_str).timestamp()
                        if line_time >= cutoff_time:
                            errors.append(line.strip())
                    except:
                        errors.append(line.strip())
    except Exception as e:
        errors.append(f"Ошибка чтения лог-файла: {e}")
    
    return errors


def _send_email_alert(subject: str, body: str) -> None:
    """Отправка email уведомления администратору"""
    if not getattr(settings, "smtp_host", None):
        print(f"\n[DEV EMAIL ALERT] {subject}\n{body}\n")
        return

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart()
    msg['From'] = getattr(settings, "smtp_user", "noreply@example.com")
    msg['To'] = getattr(settings, "admin_email", "admin@example.com")
    msg['Subject'] = f"[ALERT] {subject}"

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if getattr(settings, "smtp_tls", False):
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка отправки email администратору: {e}")


def _notify_admin(message: str, error_type: str = "general") -> None:
    """Отправка уведомления администратору (файл + email)"""
    
    
    log_path = Path(__file__).resolve().parents[2] / 'logs' / 'monitoring.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now(timezone.utc).isoformat()} {message}\n')
    
    last_time = _get_last_notification_time(error_type)
    now = datetime.now(timezone.utc)
    
    if last_time is None or (now - last_time).seconds > 3600:
        recent_errors = _get_recent_errors_from_file(error_type, hours=1, limit=15)
        
        subject = f"ADMIN_ALERT: {error_type}"
        body = f"Время: {now.isoformat()}\n"
        body += f"Сообщение: {message}\n\n"
        body += "=== Последние записи в логе (за 1 час) ===\n"
        
        if recent_errors:
            for err in recent_errors[:15]:
                body += f"{err}\n"
        else:
            body += "Нет записей в лог-файле\n"
        
        body += "\n---\n"
        body += "Полный лог доступен в файле: backend/logs/monitoring.log\n"
        
        _send_email_alert(subject, body)
        _set_last_notification_time(error_type, now)


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
                alert_details = f'Ошибка: {error_count} за последний час (тип: {event_type})'
                db.add(SystemEvent(event_type=ALERT_EVENT_TYPE, details=alert_details))
                db.commit()
                _notify_admin(f'ADMIN_ALERT {alert_details}', event_type)
    except SQLAlchemyError as exc:
        db.rollback()
        _notify_admin(f'ADMIN_ALERT мониторинг недоступен: {str(exc)[:200]}', "db_error")
    finally:
        db.close()
