from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.errors import register_exception_handlers
from app.core.config import settings
from app.routers import auth, files, admin, audit, users, share

app = FastAPI(title='Secure File Share')

origins = [origin.strip() for origin in settings.cors_allow_origins.split(',') if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

register_exception_handlers(app)


@app.on_event('startup')
def on_startup():
    Path('backend/logs').mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get('/health')
def health():
    return {'status': 'ok'}


app.include_router(auth.router)
app.include_router(files.router)
app.include_router(files.public_router)
app.include_router(files.links_router)
app.include_router(admin.router)
app.include_router(audit.router)
app.include_router(users.router)
app.include_router(share.router)
