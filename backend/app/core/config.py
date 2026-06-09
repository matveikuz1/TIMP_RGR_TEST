from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_tls: bool = False
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Secure File Share'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 20
    algorithm: str = 'HS256'
    admin_email: str = "Gasdonos@yandex.ru"
    database_url: str = 'postgresql+psycopg2://postgres:postgres@postgres:5432/filesdb'

    uploads_dir: str = str(Path(__file__).resolve().parents[2] / 'uploads')
    max_file_size_mb: int = 100
    allowed_mime_types: str = 'image/jpeg,image/png,audio/mpeg,video/mp4,video/x-msvideo,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/zip,application/pdf,text/plain'

    cookie_name: str = 'access_token'
    cookie_secure: bool = True
    cookie_samesite: str = 'strict'

    cors_allow_origins: str = 'http://localhost'
    
    # Настройки refresh token (добавлено)
    refresh_token_expire_days: int = 30  # Refresh token живёт 30 дней
    refresh_token_name: str = 'refresh_token'  # Имя cookie для refresh token

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"[DEBUG] DATABASE_URL loaded: {self.database_url}")


settings = Settings()
