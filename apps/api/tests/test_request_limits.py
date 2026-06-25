from fastapi import FastAPI
from fastapi.testclient import TestClient

from cat_api.main import MaxBodySizeMiddleware


def _build_client(max_bytes: int) -> TestClient:
    app = FastAPI()
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    def echo(payload: dict) -> dict:
        return payload

    return TestClient(app)


def test_rejects_request_body_over_limit() -> None:
    client = _build_client(max_bytes=16)

    response = client.post("/echo", json={"value": "x" * 256})

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body is too large."


def test_allows_request_body_within_limit() -> None:
    client = _build_client(max_bytes=4096)

    response = client.post("/echo", json={"value": "ok"})

    assert response.status_code == 200
    assert response.json() == {"value": "ok"}
