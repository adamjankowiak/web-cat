from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import cat_api.models  # noqa: F401
from cat_api.db.session import Base, get_session
from cat_api.main import app
from cat_api.models.document import Document, Project, Segment
from cat_api.models.translation_memory import TranslationMemoryEntry
from cat_api.services.translation_memory import (
    normalize_source_text,
    save_translation_memory_entry,
    search_translation_memory,
)


def test_normalize_source_text_collapses_whitespace_and_case() -> None:
    assert normalize_source_text("  Save\u00a0\u00a0the FILE.  ") == "save the file."


def test_save_translation_memory_entry_is_idempotent_for_same_pair() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        first_entry = save_translation_memory_entry(
            session,
            source_language="en",
            target_language="pl",
            source_text="Save the file.",
            target_text="Zapisz plik.",
        )
        second_entry = save_translation_memory_entry(
            session,
            source_language="en",
            target_language="pl",
            source_text="  save   the file. ",
            target_text="Zapisz plik.",
        )
        session.commit()

        assert first_entry.id == second_entry.id
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 1

    app.dependency_overrides.clear()
    client.close()


def test_translation_memory_search_returns_exact_match() -> None:
    client = _build_test_client()[0]

    create_response = client.post(
        "/translation-memory/entries",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file.",
            "target_text": "Zapisz plik.",
            "domain": "software",
        },
    )
    assert create_response.status_code == 201

    response = client.post(
        "/translation-memory/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "  SAVE the file. ",
            "domain": "software",
        },
    )

    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert suggestions[0]["score"] == 100
    assert suggestions[0]["match_type"] == "exact"
    assert suggestions[0]["entry"]["target_text"] == "Zapisz plik."

    app.dependency_overrides.clear()
    client.close()


def test_translation_memory_search_returns_sorted_fuzzy_matches() -> None:
    client = _build_test_client()[0]

    for source_text, target_text in [
        ("Save the file before closing the window.", "Zapisz plik przed zamknieciem okna."),
        (
            "Draft translations are saved automatically.",
            "Tlumaczenia robocze sa zapisywane automatycznie.",
        ),
    ]:
        response = client.post(
            "/translation-memory/entries",
            json={
                "source_language": "en",
                "target_language": "pl",
                "source_text": source_text,
                "target_text": target_text,
                "domain": "software",
            },
        )
        assert response.status_code == 201

    response = client.post(
        "/translation-memory/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file before closing the application.",
            "domain": "software",
            "min_score": 20,
            "limit": 5,
        },
    )

    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert len(suggestions) == 2
    assert [suggestion["match_type"] for suggestion in suggestions] == ["fuzzy", "fuzzy"]
    assert suggestions[0]["score"] >= suggestions[1]["score"]
    assert suggestions[0]["entry"]["source_text"] == "Save the file before closing the window."

    app.dependency_overrides.clear()
    client.close()


def test_translation_memory_search_returns_no_result_below_min_score() -> None:
    client = _build_test_client()[0]

    create_response = client.post(
        "/translation-memory/entries",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file.",
            "target_text": "Zapisz plik.",
        },
    )
    assert create_response.status_code == 201

    response = client.post(
        "/translation-memory/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "The contract expires next Friday.",
            "min_score": 80,
        },
    )

    assert response.status_code == 200
    assert response.json()["suggestions"] == []

    app.dependency_overrides.clear()
    client.close()


def test_service_search_suggestions_includes_exact_and_fuzzy() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        save_translation_memory_entry(
            session,
            source_language="en",
            target_language="pl",
            source_text="Save the file.",
            target_text="Zapisz plik.",
        )
        save_translation_memory_entry(
            session,
            source_language="en",
            target_language="pl",
            source_text="Save the file before closing the window.",
            target_text="Zapisz plik przed zamknieciem okna.",
        )
        session.commit()

        suggestions = search_translation_memory(
            session,
            source_language="en",
            target_language="pl",
            source_text="Save the file.",
            min_score=50,
        )

    assert suggestions[0].score == 100
    assert suggestions[0].match_type == "exact"
    assert any(suggestion.match_type == "fuzzy" for suggestion in suggestions[1:])

    app.dependency_overrides.clear()
    client.close()


def test_approve_segment_stores_translation_memory_entry() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        segment_id = _create_segment(
            session,
            source_text="Save the file.",
            target_text="Zapisz plik.",
            domain="software",
        )

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    with testing_session() as session:
        entries = session.scalars(select(TranslationMemoryEntry)).all()
        assert len(entries) == 1
        assert entries[0].source_text == "Save the file."
        assert entries[0].target_text == "Zapisz plik."
        assert entries[0].domain == "software"

    second_response = client.post(f"/segments/{segment_id}/approve")
    assert second_response.status_code == 200

    with testing_session() as session:
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 1

    app.dependency_overrides.clear()
    client.close()


def test_approve_segment_without_target_text_returns_validation_error() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        segment_id = _create_segment(
            session,
            source_text="Close the window.",
            target_text="",
            domain="software",
        )

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 400
    assert "target text" in response.json()["detail"]

    app.dependency_overrides.clear()
    client.close()


def _build_test_client() -> tuple[TestClient, sessionmaker[Session]]:
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
    return TestClient(app), testing_session


def _create_segment(
    session: Session,
    *,
    source_text: str,
    target_text: str,
    domain: str | None,
) -> str:
    project = Project(
        name="Sample",
        source_language="en",
        target_language="pl",
        domain=domain,
    )
    document = Document(
        project=project,
        filename="sample.txt",
        source_language="en",
        target_language="pl",
        status="imported",
    )
    segment = Segment(
        document=document,
        position=1,
        source_text=source_text,
        target_text=target_text,
        status="draft",
    )
    session.add(segment)
    session.commit()
    return str(segment.id)
