from collections.abc import Iterator
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import cat_api.models  # noqa: F401
from cat_api.db.session import Base, get_session
from cat_api.main import app
from cat_api.models.document import Document, Project, Segment
from cat_api.models.glossary import GlossaryTerm
from cat_api.models.translation_memory import TranslationMemoryEntry


def test_glossary_search_returns_single_word_term_with_position() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        _create_term(session, source_term="file", target_term="plik")

    response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file before closing.",
        },
    )

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["term"]["source_term"] == "file"
    assert matches[0]["term"]["target_term"] == "plik"
    assert matches[0]["start"] == 9
    assert matches[0]["end"] == 13

    _close_test_client(client)


def test_glossary_search_returns_multi_word_term() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        _create_term(
            session,
            source_term="translation memory",
            target_term="pamiec tlumaczen",
        )

    response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "The translation memory panel is open.",
        },
    )

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["matched_text"] == "translation memory"

    _close_test_client(client)


def test_glossary_search_filters_by_languages_domain_and_project() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Software", source_language="en", target_language="pl")
        other_project = Project(name="Legal", source_language="en", target_language="pl")
        session.add_all([project, other_project])
        session.flush()
        _create_term(
            session,
            source_term="window",
            target_term="okno",
            domain="software",
            project_id=project.id,
        )
        _create_term(
            session,
            source_term="window",
            target_term="termin prawny",
            domain="legal",
            project_id=project.id,
        )
        _create_term(
            session,
            source_term="window",
            target_term="fenetre",
            source_language="en",
            target_language="fr",
            domain="software",
            project_id=project.id,
        )
        _create_term(
            session,
            source_term="window",
            target_term="inne okno",
            domain="software",
            project_id=other_project.id,
        )
        session.commit()
        project_id = str(project.id)

    response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Close the window.",
            "domain": "software",
            "project_id": project_id,
        },
    )

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert [match["term"]["target_term"] for match in matches] == ["okno"]

    _close_test_client(client)


def test_glossary_search_respects_case_sensitive_terms() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        _create_term(
            session,
            source_term="API",
            target_term="API",
            case_sensitive=True,
        )

    lower_response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Call the api.",
        },
    )
    upper_response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Call the API.",
        },
    )

    assert lower_response.status_code == 200
    assert lower_response.json()["matches"] == []
    assert upper_response.status_code == 200
    assert len(upper_response.json()["matches"]) == 1

    _close_test_client(client)


def test_glossary_search_returns_forbidden_term() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        _create_term(
            session,
            source_term="click here",
            target_term="kliknij tutaj",
            forbidden=True,
        )

    response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Do not write click here in UI text.",
        },
    )

    assert response.status_code == 200
    assert response.json()["matches"][0]["term"]["forbidden"] is True

    _close_test_client(client)


def test_glossary_terms_crud() -> None:
    client = _build_test_client()[0]

    create_response = client.post(
        "/glossary/terms",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_term": "draft",
            "target_term": "wersja robocza",
            "domain": "software",
        },
    )
    assert create_response.status_code == 201
    term_id = create_response.json()["id"]

    list_response = client.get(
        "/glossary/terms",
        params={"source_language": "en", "target_language": "pl", "domain": "software"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    patch_response = client.patch(
        f"/glossary/terms/{term_id}",
        json={"target_term": "roboczy", "definition": "Working status."},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["target_term"] == "roboczy"

    delete_response = client.delete(f"/glossary/terms/{term_id}")
    assert delete_response.status_code == 204
    assert client.get("/glossary/terms").json() == []

    _close_test_client(client)


def test_glossary_import_csv_creates_terms() -> None:
    client = _build_test_client()[0]
    csv_content = (
        "source_term,target_term,source_language,target_language,definition,domain,"
        "case_sensitive,forbidden,example_source,example_target\n"
        "Save,Zapisz,en,pl,Button label,software,true,false,Save the file.,Zapisz plik.\n"
        "click here,kliknij tutaj,en,pl,Avoid this phrase,software,false,true,,\n"
    )

    response = client.post(
        "/glossary/import-csv",
        content=csv_content,
        headers={"Content-Type": "text/csv"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["imported_count"] == 2
    assert payload["terms"][0]["case_sensitive"] is True
    assert payload["terms"][1]["forbidden"] is True

    _close_test_client(client)


def test_glossary_import_csv_validates_required_columns() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/glossary/import-csv",
        content="source_term,target_term\nSave,Zapisz\n",
        headers={"Content-Type": "text/csv"},
    )

    assert response.status_code == 400
    assert "source_language" in response.json()["detail"]
    assert "target_language" in response.json()["detail"]

    _close_test_client(client)


def test_approve_segment_succeeds_when_required_target_term_is_present() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        segment_id = _create_segment(
            session,
            source_text="Save the file.",
            target_text="Zapisz plik.",
            domain="software",
        )
        _create_term(
            session,
            source_term="file",
            target_term="plik",
            domain="software",
        )

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    with testing_session() as session:
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 1

    _close_test_client(client)


def test_approve_segment_fails_when_required_target_term_is_missing() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        segment_id = _create_segment(
            session,
            source_text="Save the file.",
            target_text="Zapisz dokument.",
            domain="software",
        )
        _create_term(
            session,
            source_term="file",
            target_term="plik",
            domain="software",
        )

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 409
    violations = response.json()["detail"]["violations"]
    assert violations[0]["violation_type"] == "missing_required"

    with testing_session() as session:
        segment = session.get(Segment, segment_id)
        assert segment is not None
        assert segment.status == "draft"
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 0

    _close_test_client(client)


def test_approve_segment_fails_when_forbidden_target_term_is_present() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        segment_id = _create_segment(
            session,
            source_text="Avoid click here.",
            target_text="Unikaj kliknij tutaj.",
            domain="software",
        )
        _create_term(
            session,
            source_term="click here",
            target_term="kliknij tutaj",
            domain="software",
            forbidden=True,
        )

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 409
    violations = response.json()["detail"]["violations"]
    assert violations[0]["violation_type"] == "forbidden_present"

    with testing_session() as session:
        segment = session.get(Segment, segment_id)
        assert segment is not None
        assert segment.status == "draft"
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 0

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


def _create_term(
    session: Session,
    *,
    source_term: str,
    target_term: str,
    source_language: str = "en",
    target_language: str = "pl",
    domain: str | None = None,
    project_id: UUID | None = None,
    case_sensitive: bool = False,
    forbidden: bool = False,
) -> GlossaryTerm:
    term = GlossaryTerm(
        source_language=source_language,
        target_language=target_language,
        source_term=source_term,
        target_term=target_term,
        domain=domain,
        project_id=project_id,
        case_sensitive=case_sensitive,
        forbidden=forbidden,
    )
    session.add(term)
    session.commit()
    return term


def _create_segment(
    session: Session,
    *,
    source_text: str,
    target_text: str,
    domain: str | None,
) -> UUID:
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
    return segment.id
