import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['COOKIE_SECURE'] = 'false'

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.core import models  # noqa: F401

db_file = Path(__file__).resolve().parents[1] / 'test.db'
if db_file.exists():
    db_file.unlink()
Base.metadata.create_all(bind=engine)

client = TestClient(app)
