import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from cat_api.api.routes import demo
from cat_api.models.document import Document
from cat_api.models.glossary import GlossaryTerm
from cat_api.models.translation_memory import TranslationMemoryEntry


def test_demo_seed_loads_sample_document_memory_and_glossary(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = test_client

    response = client.post("/demo/seed")

    assert response.status_code == 201
    payload = response.json()
    assert payload["translation_memory_count"] == 2
    assert payload["glossary_count"] == 4
    assert payload["document"]["document"]["filename"] == "software-cat-source.txt"
    assert [segment["source_text"] for segment in payload["document"]["segments"]] == [
        "Save the file.",
        "Save the file before closing the window.",
        "Open the translation memory panel.",
        "Check the target segment for spelling errors.",
    ]

    second_response = client.post("/demo/seed")
    assert second_response.status_code == 201
    assert second_response.json()["document"]["document"]["id"] == payload["document"]["document"]["id"]

    with testing_session() as session:
        assert len(session.scalars(select(Document)).all()) == 1
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 2
        assert len(session.scalars(select(GlossaryTerm)).all()) == 4


def test_demo_seed_missing_samples_returns_generic_error(
    test_client: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = test_client
    leaked_path = "/srv/app/data/samples/documents/software-cat-source.txt"

    def _raise_missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError(f"Demo sample file was not found: {leaked_path}")

    monkeypatch.setattr(demo, "seed_demo_data", _raise_missing)

    response = client.post("/demo/seed")

    assert response.status_code == 500
    assert response.json()["detail"] == "Demo sample data is unavailable on the server."
    assert leaked_path not in response.text
