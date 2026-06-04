import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_2fa_code(email: str, code: str) -> None:
    if not getattr(settings, "smtp_host", None):
        print(f"\n[DEV EMAIL] Код 2FA для {email}: {code}\n")
        return

    msg = MIMEMultipart()
    msg['From'] = getattr(settings, "smtp_user", "noreply@example.com")
    msg['To'] = email
    msg['Subject'] = "Код подтверждения двухфакторной аутентификации"

    body = f"Ваш код подтверждения: {code}. Он действителен в течение 5 минут."
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if getattr(settings, "smtp_tls", False):
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
