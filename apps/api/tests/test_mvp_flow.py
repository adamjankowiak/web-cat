from xml.etree import ElementTree

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from cat_api.models.glossary import GlossaryTerm
from cat_api.models.translation_memory import TranslationMemoryEntry


def test_mvp_flow_from_import_to_tm_glossary_spellcheck_and_exports(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = test_client

    imported_tbx = client.post(
        "/glossary/import-tbx",
        content=_sample_tbx(),
        headers={"Content-Type": "application/xml"},
    )
    assert imported_tbx.status_code == 201
    assert imported_tbx.json()["imported_count"] == 2

    imported_tmx = client.post(
        "/translation-memory/import-tmx",
        content=_sample_tmx(),
        headers={"Content-Type": "application/xml"},
    )
    assert imported_tmx.status_code == 201
    assert imported_tmx.json()["imported_count"] == 1

    document_response = client.post(
        "/documents",
        json={
            "filename": "mvp-demo.txt",
            "content": (
                "Save the file. "
                "Save the file before closing the window. "
                "Open the translation memory panel."
            ),
            "source_language": "en",
            "target_language": "pl",
            "project_name": "MVP Demo",
            "segmentation_strategy": "sentence",
        },
    )
    assert document_response.status_code == 201
    document_payload = document_response.json()
    document_id = document_payload["document"]["id"]
    first_segment_id = document_payload["segments"][0]["id"]
    second_segment_id = document_payload["segments"][1]["id"]
    assert [segment["source_text"] for segment in document_payload["segments"]] == [
        "Save the file.",
        "Save the file before closing the window.",
        "Open the translation memory panel.",
    ]

    draft_response = client.patch(
        f"/segments/{first_segment_id}",
        json={"target_text": "Zapisz plik."},
    )
    assert draft_response.status_code == 200
    assert draft_response.json()["status"] == "draft"

    approve_response = client.post(f"/segments/{first_segment_id}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    tm_response = client.post(
        "/translation-memory/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file before closing the window.",
            "min_score": 20,
            "limit": 5,
        },
    )
    assert tm_response.status_code == 200
    suggestions = tm_response.json()["suggestions"]
    assert suggestions[0]["entry"]["target_text"] == "Zapisz plik przed zamknieciem okno."
    assert any(suggestion["entry"]["target_text"] == "Zapisz plik." for suggestion in suggestions)

    glossary_response = client.post(
        "/glossary/search",
        json={
            "source_language": "en",
            "target_language": "pl",
            "source_text": "Save the file before closing the window.",
        },
    )
    assert glossary_response.status_code == 200
    assert [match["term"]["source_term"] for match in glossary_response.json()["matches"]] == [
        "file",
        "window",
    ]

    terminology_failure = client.patch(
        f"/segments/{second_segment_id}",
        json={"target_text": "Zapisz dokument przed zamknieciem ekranu."},
    )
    assert terminology_failure.status_code == 200
    approval_failure = client.post(f"/segments/{second_segment_id}/approve")
    assert approval_failure.status_code == 409
    assert approval_failure.json()["detail"]["violations"][0]["violation_type"] == "missing_required"

    spellcheck_response = client.post(
        "/spellcheck",
        json={"language": "pl", "text": "To jest tlumacznie docelowe."},
    )
    assert spellcheck_response.status_code == 200
    assert spellcheck_response.json()["issues"][0]["suggestions"][0]["value"] == "tlumaczenie"

    fixed_second_segment = client.patch(
        f"/segments/{second_segment_id}",
        json={"target_text": "Zapisz plik przed zamknieciem okno."},
    )
    assert fixed_second_segment.status_code == 200
    second_approval = client.post(f"/segments/{second_segment_id}/approve")
    assert second_approval.status_code == 200

    txt_response = client.get(f"/documents/{document_id}/export.txt")
    assert txt_response.status_code == 200
    assert txt_response.text == (
        "Zapisz plik.\n"
        "Zapisz plik przed zamknieciem okno.\n"
        "Open the translation memory panel."
    )

    exported_tmx = client.get("/translation-memory/export.tmx")
    assert exported_tmx.status_code == 200
    assert _count_xml_elements(exported_tmx.text, "tu") == 3

    exported_tbx = client.get("/glossary/export.tbx")
    assert exported_tbx.status_code == 200
    assert _count_xml_elements(exported_tbx.text, "termEntry") == 2

    with testing_session() as session:
        assert len(session.scalars(select(TranslationMemoryEntry)).all()) == 3
        assert len(session.scalars(select(GlossaryTerm)).all()) == 2


def _sample_tmx() -> str:
    return """
    <tmx version="1.4">
      <header creationtool="web-cat" srclang="en" adminlang="en" datatype="PlainText" />
      <body>
        <tu>
          <tuv xml:lang="en"><seg>Save the file before closing the window.</seg></tuv>
          <tuv xml:lang="pl"><seg>Zapisz plik przed zamknieciem okno.</seg></tuv>
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
            <descrip type="definition">A document stored by the application.</descrip>
            <langSet xml:lang="en"><tig><term>file</term></tig></langSet>
            <langSet xml:lang="pl"><tig><term>plik</term></tig></langSet>
          </termEntry>
          <termEntry>
            <descrip type="definition">Application frame shown on screen.</descrip>
            <langSet xml:lang="en"><tig><term>window</term></tig></langSet>
            <langSet xml:lang="pl"><tig><term>okno</term></tig></langSet>
          </termEntry>
        </body>
      </text>
    </tbx>
    """


def _count_xml_elements(xml_content: str, name: str) -> int:
    root = ElementTree.fromstring(xml_content)
    return sum(1 for element in root.iter() if _local_name(element.tag) == name)


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[1]

    return tag
