import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from pathlib import Path

from app.services.monitoring import record_error

class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={'error': True, 'code': 'VALIDATION_ERROR', 'message': 'Некорректные входные данные'},
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={'error': True, 'code': exc.code, 'message': exc.message})

    @app.exception_handler(OperationalError)
    async def db_error_handler(_: Request, exc: OperationalError):
        error_id = str(uuid.uuid4())
        log_path = Path(__file__).resolve().parents[2] / 'logs' / 'system_events.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'DB_UNAVAILABLE {error_id} {str(exc)[:300]}\n')
        record_error('ERROR', f'DB_UNAVAILABLE {error_id} {str(exc)[:300]}')
        return JSONResponse(
            status_code=503,
            content={'error': True, 'code': 'DB_UNAVAILABLE', 'message': 'Внутренняя ошибка сервера', 'error_id': error_id},
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError):
        error_id = str(uuid.uuid4())
        record_error('ERROR', f'SQLALCHEMY_ERROR {error_id} {str(exc)[:300]}')
        return JSONResponse(
            status_code=500,
            content={'error': True, 'code': 'INTERNAL_ERROR', 'message': 'Внутренняя ошибка сервера', 'error_id': error_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception):
        error_id = str(uuid.uuid4())
        record_error('ERROR', f'UNHANDLED_ERROR {error_id}')
        return JSONResponse(
            status_code=500,
            content={'error': True, 'code': 'INTERNAL_ERROR', 'message': 'Внутренняя ошибка сервера', 'error_id': error_id},
        )
