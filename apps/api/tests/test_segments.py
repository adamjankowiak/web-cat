from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from cat_api.models.document import Document, Project, Segment


def _create_segment(
    testing_session: sessionmaker[Session],
    *,
    locked: bool = False,
    target_text: str | None = None,
) -> str:
    with testing_session() as session:
        project = Project(name="Sample", source_language="en", target_language="pl")
        document = Document(
            project=project,
            filename="sample.txt",
            source_language="en",
            target_language="pl",
            status="imported",
        )
        document.segments = [
            Segment(
                position=1,
                source_text="Save the file.",
                target_text=target_text,
                locked=locked,
            )
        ]
        session.add(document)
        session.commit()
        return str(document.segments[0].id)


def test_update_segment_returns_404_for_unknown_id(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = test_client

    response = client.patch(f"/segments/{uuid4()}", json={"target_text": "Zapisz plik."})

    assert response.status_code == 404
    assert response.json()["detail"] == "Segment was not found."


def test_update_locked_segment_returns_409(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = test_client
    segment_id = _create_segment(testing_session, locked=True)

    response = client.patch(f"/segments/{segment_id}", json={"target_text": "Zapisz plik."})

    assert response.status_code == 409
    assert "Locked segment" in response.json()["detail"]


def test_approve_locked_segment_returns_409(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = test_client
    segment_id = _create_segment(testing_session, locked=True, target_text="Zapisz plik.")

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 409
    assert "Locked segment" in response.json()["detail"]


def test_approve_without_target_text_returns_400(
    test_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = test_client
    segment_id = _create_segment(testing_session, target_text=None)

    response = client.post(f"/segments/{segment_id}/approve")

    assert response.status_code == 400
    assert "without target text" in response.json()["detail"]
