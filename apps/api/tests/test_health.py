from fastapi.testclient import TestClient

from cat_api.main import app


def test_healthcheck_returns_api_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "cat-api",
        "version": "0.1.0",
    }
