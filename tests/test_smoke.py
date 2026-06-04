from fastapi.testclient import TestClient

from backend.api import create_app


def test_health():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "adamsy-free-tv-api"


def test_channels_list():
    app = create_app()
    client = TestClient(app)
    response = client.get("/channels")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
