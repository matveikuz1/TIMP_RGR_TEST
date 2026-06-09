import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if os.environ.get('CI'):
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/testdb')
else:
    os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

os.environ['COOKIE_SECURE'] = 'false'

os.environ['TESTING'] = 'true'

os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['COOKIE_SECURE'] = 'false'

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.core import models
Base.metadata.create_all(bind=engine)

client = TestClient(app)
