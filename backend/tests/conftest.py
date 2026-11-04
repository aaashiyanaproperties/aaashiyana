import os
from pathlib import Path
DB_PATH='/tmp/aashiyana-pytest.db'
try: Path(DB_PATH).unlink()
except FileNotFoundError: pass
os.environ['DATABASE_URL']=f'sqlite+pysqlite:///{DB_PATH}'
os.environ['DEV_AUTH_BYPASS']='true'
os.environ['ENVIRONMENT']='development'
import pytest
from fastapi.testclient import TestClient
from app.main import app
@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c: yield c
