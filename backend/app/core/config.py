from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Secure File Share'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 20
    algorithm: str = 'HS256'

    database_url: str = 'postgresql+psycopg2://postgres:postgres@postgres:5432/filesdb'

    uploads_dir: str = str(Path(__file__).resolve().parents[2] / 'uploads')
    max_file_size_mb: int = 100
    allowed_mime_types: str = 'image/jpeg,image/png,audio/mpeg,video/mp4,video/x-msvideo,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/zip,application/pdf,text/plain'

    cookie_name: str = 'access_token'
    cookie_secure: bool = True
    cookie_samesite: str = 'strict'

    cors_allow_origins: str = 'http://localhost'

settings = Settings()
