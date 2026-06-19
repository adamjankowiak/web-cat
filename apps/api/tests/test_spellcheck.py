from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import cat_api.models  # noqa: F401
from cat_api.db.session import Base, get_session
from cat_api.main import app
from cat_api.models.document import Project
from cat_api.models.spellcheck import SpellcheckIgnore


def test_spellcheck_returns_polish_target_text_issue_with_position_and_suggestions() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/spellcheck",
        json={"language": "pl", "text": "To jest tlumacznie docelowe."},
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["token"] == "tlumacznie"
    assert issues[0]["start"] == 8
    assert issues[0]["end"] == 18
    assert issues[0]["language"] == "pl"
    assert issues[0]["rule_code"] == "LOCAL_DICTIONARY_UNKNOWN_WORD"
    assert issues[0]["suggestions"][0]["value"] == "tlumaczenie"

    _close_test_client(client)


def test_spellcheck_returns_english_target_text_issue() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/spellcheck",
        json={"language": "en", "text": "Ths file is saved."},
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["token"] == "Ths"
    assert issues[0]["suggestions"][0]["value"] == "this"

    _close_test_client(client)


def test_spellcheck_returns_german_target_text_issue() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/spellcheck",
        json={"language": "de", "text": "Speichern Sie die Dateii."},
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["token"] == "Dateii"
    assert issues[0]["suggestions"][0]["value"] == "datei"

    _close_test_client(client)


def test_spellcheck_results_are_deterministic() -> None:
    client = _build_test_client()[0]

    payload = {"language": "pl", "text": "To jest tlumacznie docelowe."}
    first_response = client.post("/spellcheck", json=payload)
    second_response = client.post("/spellcheck", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()

    _close_test_client(client)


def test_spellcheck_does_not_flag_known_words_for_supported_languages() -> None:
    client = _build_test_client()[0]

    examples = [
        {"language": "pl", "text": "Zapisz plik."},
        {"language": "en", "text": "Save the file."},
        {"language": "de", "text": "Speichern Sie die Datei."},
    ]

    for payload in examples:
        response = client.post("/spellcheck", json=payload)
        assert response.status_code == 200
        assert response.json()["issues"] == []

    _close_test_client(client)


def test_spellcheck_unsupported_language_returns_clear_error() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/spellcheck",
        json={"language": "es", "text": "Texto correcto."},
    )

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]

    _close_test_client(client)


def test_spellcheck_ignore_word_for_project_removes_issue_from_results() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Software", source_language="en", target_language="pl")
        session.add(project)
        session.commit()
        project_id = str(project.id)

    first_response = client.post(
        "/spellcheck",
        json={
            "language": "pl",
            "text": "To jest WebCAT docelowe.",
            "project_id": project_id,
        },
    )
    assert first_response.status_code == 200
    assert [issue["token"] for issue in first_response.json()["issues"]] == ["WebCAT"]

    ignore_response = client.post(
        "/spellcheck/ignore",
        json={"project_id": project_id, "language": "pl", "word": "WebCAT"},
    )
    assert ignore_response.status_code == 201
    assert ignore_response.json()["word"] == "webcat"

    second_response = client.post(
        "/spellcheck",
        json={
            "language": "pl",
            "text": "To jest WebCAT docelowe.",
            "project_id": project_id,
        },
    )
    assert second_response.status_code == 200
    assert second_response.json()["issues"] == []

    list_response = client.get(
        "/spellcheck/ignore",
        params={"project_id": project_id, "language": "pl"},
    )
    assert list_response.status_code == 200
    assert [ignored["word"] for ignored in list_response.json()] == ["webcat"]

    _close_test_client(client)


def test_spellcheck_ignore_word_creation_is_idempotent() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Software", source_language="en", target_language="pl")
        session.add(project)
        session.commit()
        project_id = str(project.id)

    first_response = client.post(
        "/spellcheck/ignore",
        json={"project_id": project_id, "language": "PL", "word": "WebCAT"},
    )
    second_response = client.post(
        "/spellcheck/ignore",
        json={"project_id": project_id, "language": "pl", "word": "webcat"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] == second_response.json()["id"]

    with testing_session() as session:
        assert len(session.scalars(select(SpellcheckIgnore)).all()) == 1

    _close_test_client(client)


def test_spellcheck_delete_ignored_word() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Software", source_language="en", target_language="pl")
        session.add(project)
        session.flush()
        ignored_word = SpellcheckIgnore(project_id=project.id, language="pl", word="webcat")
        session.add(ignored_word)
        session.commit()
        ignored_word_id = str(ignored_word.id)
        project_id = str(project.id)

    delete_response = client.delete(f"/spellcheck/ignore/{ignored_word_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/spellcheck/ignore", params={"project_id": project_id})
    assert list_response.status_code == 200
    assert list_response.json() == []

    _close_test_client(client)


def test_spellcheck_validates_empty_text() -> None:
    client = _build_test_client()[0]

    response = client.post("/spellcheck", json={"language": "pl", "text": "   "})

    assert response.status_code == 422

    _close_test_client(client)


def test_spellcheck_validates_missing_language() -> None:
    client = _build_test_client()[0]

    response = client.post("/spellcheck", json={"text": "To jest tekst."})

    assert response.status_code == 422

    _close_test_client(client)


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


def _close_test_client(client: TestClient) -> None:
    app.dependency_overrides.clear()
    client.close()
