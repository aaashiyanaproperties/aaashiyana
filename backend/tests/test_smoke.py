from fastapi.testclient import TestClient
from app.main import app

def test_health():
    response=TestClient(app).get("/api/health")
    assert response.status_code==200
    assert response.json()["status"]=="ok"

def test_guest_search():
    response=TestClient(app).get("/api/properties",params={"city":"Pune"})
    assert response.status_code==200
    assert "items" in response.json()
