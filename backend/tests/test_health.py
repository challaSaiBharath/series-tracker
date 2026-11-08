from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="http://localhost")


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
