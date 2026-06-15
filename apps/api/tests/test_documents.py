from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import cat_api.models  # noqa: F401
from cat_api.db.session import Base, get_session
from cat_api.main import app


def test_import_txt_document_creates_segments_and_saves_draft() -> None:
    client = _build_test_client()

    response = client.post(
        "/documents",
        json={
            "filename": "sample.txt",
            "content": "Save the file. Close the window.",
            "source_language": "en",
            "target_language": "pl",
            "segmentation_strategy": "sentence",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["filename"] == "sample.txt"
    assert payload["document"]["status"] == "imported"
    assert [segment["source_text"] for segment in payload["segments"]] == [
        "Save the file.",
        "Close the window.",
    ]
    assert {segment["status"] for segment in payload["segments"]} == {"new"}

    segment_id = payload["segments"][0]["id"]
    draft_response = client.patch(
        f"/segments/{segment_id}",
        json={"target_text": "Zapisz plik."},
    )

    assert draft_response.status_code == 200
    assert draft_response.json()["target_text"] == "Zapisz plik."
    assert draft_response.json()["status"] == "draft"

    app.dependency_overrides.clear()


def _build_test_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_session() -> Iterator[Session]:
        session = testing_session()

        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)
