from collections.abc import Iterator
from xml.etree import ElementTree

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
from cat_api.services.translation_memory import save_translation_memory_entry


def test_export_txt_uses_target_text_in_segment_order() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        document = _create_document(
            session,
            segments=[
                Segment(position=2, source_text="Second source.", target_text="Drugi."),
                Segment(position=1, source_text="First source.", target_text="Pierwszy."),
            ],
        )
        document_id = str(document.id)

    response = client.get(f"/documents/{document_id}/export.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "sample.txt" in response.headers["content-disposition"]
    assert response.text == "Pierwszy.\nDrugi."

    _close_test_client(client)


def test_export_txt_falls_back_to_source_text_when_target_is_missing() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        document = _create_document(
            session,
            segments=[
                Segment(position=1, source_text="Translated source.", target_text="Tlumaczenie."),
                Segment(position=2, source_text="Missing target.", target_text=None),
            ],
        )
        document_id = str(document.id)

    response = client.get(f"/documents/{document_id}/export.txt")

    assert response.status_code == 200
    assert response.text == "Tlumaczenie.\nMissing target."

    _close_test_client(client)


def test_export_xliff_contains_source_target_status_and_languages() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        document = _create_document(
            session,
            segments=[
                Segment(
                    position=1,
                    source_text="Save the file.",
                    target_text="Zapisz plik.",
                    status="approved",
                )
            ],
        )
        document_id = str(document.id)

    response = client.get(f"/documents/{document_id}/export.xliff")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-xliff+xml")

    root = ElementTree.fromstring(response.text)
    file_element = _find_descendant(root, "file")
    trans_unit = _find_descendant(root, "trans-unit")
    assert file_element is not None
    assert trans_unit is not None
    assert file_element.attrib["source-language"] == "en"
    assert file_element.attrib["target-language"] == "pl"
    assert _find_descendant(trans_unit, "source").text == "Save the file."
    target = _find_descendant(trans_unit, "target")
    assert target is not None
    assert target.text == "Zapisz plik."
    assert target.attrib["state"] == "approved"

    _close_test_client(client)


def test_export_tmx_contains_translation_memory_metadata() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Sample", source_language="en", target_language="pl")
        session.add(project)
        session.flush()
        save_translation_memory_entry(
            session,
            source_language="en",
            target_language="pl",
            source_text="Save the file.",
            target_text="Zapisz plik.",
            domain="software",
            project_id=project.id,
        )
        session.commit()
        project_id = str(project.id)

    response = client.get(
        "/translation-memory/export.tmx",
        params={
            "source_language": "en",
            "target_language": "pl",
            "domain": "software",
            "project_id": project_id,
        },
    )

    assert response.status_code == 200
    root = ElementTree.fromstring(response.text)
    tu = _find_descendant(root, "tu")
    assert tu is not None
    assert tu.attrib["creationdate"]
    props = {
        prop.attrib["type"]: "".join(prop.itertext())
        for prop in tu
        if _local_name(prop.tag) == "prop"
    }
    assert props == {"domain": "software", "project_id": project_id}
    assert "Save the file." in response.text
    assert "Zapisz plik." in response.text

    _close_test_client(client)


def test_import_tmx_creates_translation_memory_entry() -> None:
    client, testing_session = _build_test_client()
    tmx = _sample_tmx()

    response = client.post(
        "/translation-memory/import-tmx",
        content=tmx,
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 1

    with testing_session() as session:
        entries = session.scalars(select(TranslationMemoryEntry)).all()
        assert len(entries) == 1
        assert entries[0].source_language == "en"
        assert entries[0].target_language == "pl"
        assert entries[0].source_text == "Save the file."
        assert entries[0].target_text == "Zapisz plik."
        assert entries[0].domain == "software"

    _close_test_client(client)


def test_import_tmx_is_idempotent() -> None:
    client, testing_session = _build_test_client()

    for _ in range(2):
        response = client.post(
            "/translation-memory/import-tmx",
            content=_sample_tmx(),
            headers={"Content-Type": "application/xml"},
        )
        assert response.status_code == 201

    with testing_session() as session:
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 1

    _close_test_client(client)


def test_import_tmx_rejects_invalid_structure() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/translation-memory/import-tmx",
        content="<tmx><body><tu /></body></tmx>",
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 400
    assert "tuv/seg" in response.json()["detail"]

    _close_test_client(client)


def test_export_tbx_contains_glossary_metadata() -> None:
    client, testing_session = _build_test_client()

    with testing_session() as session:
        project = Project(name="Sample", source_language="en", target_language="pl")
        session.add(project)
        session.flush()
        session.add(
            GlossaryTerm(
                source_language="en",
                target_language="pl",
                source_term="Save",
                target_term="Zapisz",
                definition="Button label.",
                domain="software",
                project_id=project.id,
                case_sensitive=True,
                forbidden=False,
            )
        )
        session.commit()
        project_id = str(project.id)

    response = client.get(
        "/glossary/export.tbx",
        params={
            "source_language": "en",
            "target_language": "pl",
            "domain": "software",
            "project_id": project_id,
        },
    )

    assert response.status_code == 200
    root = ElementTree.fromstring(response.text)
    term_entry = _find_descendant(root, "termEntry")
    assert term_entry is not None
    descriptions = {
        descrip.attrib["type"]: "".join(descrip.itertext())
        for descrip in term_entry
        if _local_name(descrip.tag) == "descrip"
    }
    assert descriptions["definition"] == "Button label."
    assert descriptions["domain"] == "software"
    assert descriptions["project_id"] == project_id
    assert descriptions["case_sensitive"] == "true"
    assert descriptions["forbidden"] == "false"

    _close_test_client(client)


def test_import_tbx_creates_glossary_term() -> None:
    client, testing_session = _build_test_client()

    response = client.post(
        "/glossary/import-tbx",
        content=_sample_tbx(),
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 1

    with testing_session() as session:
        terms = session.scalars(select(GlossaryTerm)).all()
        assert len(terms) == 1
        assert terms[0].source_term == "Save"
        assert terms[0].target_term == "Zapisz"
        assert terms[0].definition == "Button label."
        assert terms[0].domain == "software"
        assert terms[0].case_sensitive is True
        assert terms[0].forbidden is True

    _close_test_client(client)


def test_import_tbx_rejects_invalid_structure() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/glossary/import-tbx",
        content="<tbx><text><body><termEntry /></body></text></tbx>",
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 400
    assert "langSet/term" in response.json()["detail"]

    _close_test_client(client)


def test_import_tmx_rejects_dtd_entity_expansion() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/translation-memory/import-tmx",
        content=_entity_expansion_bomb("tmx"),
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 400
    assert "DOCTYPE" in response.json()["detail"]

    _close_test_client(client)


def test_import_tbx_rejects_dtd_entity_expansion() -> None:
    client = _build_test_client()[0]

    response = client.post(
        "/glossary/import-tbx",
        content=_entity_expansion_bomb("tbx"),
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 400
    assert "DOCTYPE" in response.json()["detail"]

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


def _create_document(
    session: Session,
    *,
    segments: list[Segment],
) -> Document:
    project = Project(name="Sample", source_language="en", target_language="pl")
    document = Document(
        project=project,
        filename="sample.txt",
        source_language="en",
        target_language="pl",
        status="imported",
    )
    document.segments = segments
    session.add(document)
    session.commit()
    return document


def _sample_tmx() -> str:
    return """
    <tmx version="1.4">
      <header creationtool="web-cat" srclang="en" adminlang="en" datatype="PlainText" />
      <body>
        <tu>
          <prop type="domain">software</prop>
          <tuv xml:lang="en"><seg>Save the file.</seg></tuv>
          <tuv xml:lang="pl"><seg>Zapisz plik.</seg></tuv>
        </tu>
      </body>
    </tmx>
    """


def _sample_tbx() -> str:
    return """
    <tbx>
      <text>
        <body>
          <termEntry>
            <descrip type="definition">Button label.</descrip>
            <descrip type="domain">software</descrip>
            <descrip type="case_sensitive">true</descrip>
            <descrip type="forbidden">true</descrip>
            <langSet xml:lang="en"><tig><term>Save</term></tig></langSet>
            <langSet xml:lang="pl"><tig><term>Zapisz</term></tig></langSet>
          </termEntry>
        </body>
      </text>
    </tbx>
    """


def _find_descendant(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((item for item in element.iter() if _local_name(item.tag) == name), None)


def _entity_expansion_bomb(root: str) -> str:
    return (
        '<?xml version="1.0"?>\n'
        f"<!DOCTYPE {root} [\n"
        '  <!ENTITY a "aaaaaaaaaa">\n'
        '  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">\n'
        "]>\n"
        f"<{root}><body><tu>"
        '<tuv xml:lang="en"><seg>&b;</seg></tuv>'
        '<tuv xml:lang="pl"><seg>&b;</seg></tuv>'
        f"</tu></body></{root}>"
    )


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[1]

    return tag
