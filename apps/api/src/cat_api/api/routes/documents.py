from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cat_api.db.session import get_session
from cat_api.models.document import Document, Project, Segment
from cat_api.schemas.document import (
    DocumentDetailRead,
    DocumentImportRequest,
    DocumentRead,
    SegmentRead,
)
from cat_api.services.segmentation import segment_text

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentDetailRead, status_code=status.HTTP_201_CREATED)
def import_txt_document(
    payload: DocumentImportRequest,
    session: Session = Depends(get_session),
) -> DocumentDetailRead:
    segments = segment_text(payload.content, payload.segmentation_strategy)

    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TXT content does not contain importable text.",
        )

    project = _resolve_project(payload, session)

    document = Document(
        project=project,
        filename=payload.filename,
        source_language=payload.source_language,
        target_language=payload.target_language,
        status="imported",
    )
    document.segments = [
        Segment(position=index, source_text=source_text, status="new")
        for index, source_text in enumerate(segments, start=1)
    ]

    session.add(document)
    session.commit()

    document = _get_document_or_404(document.id, session)
    return DocumentDetailRead(
        document=DocumentRead.model_validate(document),
        segments=_read_segments(document),
    )


@router.get("", response_model=list[DocumentRead])
def list_documents(session: Session = Depends(get_session)) -> list[Document]:
    return list(
        session.scalars(select(Document).order_by(Document.created_at.desc(), Document.filename)).all()
    )


@router.get("/{document_id}", response_model=DocumentDetailRead)
def get_document(document_id: UUID, session: Session = Depends(get_session)) -> DocumentDetailRead:
    document = _get_document_or_404(document_id, session)
    return DocumentDetailRead(
        document=DocumentRead.model_validate(document),
        segments=_read_segments(document),
    )


@router.get("/{document_id}/segments", response_model=list[SegmentRead])
def list_document_segments(
    document_id: UUID,
    session: Session = Depends(get_session),
) -> list[Segment]:
    document = _get_document_or_404(document_id, session)
    return list(document.segments)


def _resolve_project(payload: DocumentImportRequest, session: Session) -> Project:
    if payload.project_id is not None:
        project = session.get(Project, payload.project_id)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project was not found.",
            )

        return project

    filename_stem = payload.filename.rsplit(".", maxsplit=1)[0]
    project_name = payload.project_name or filename_stem or payload.filename
    return Project(
        name=project_name,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )


def _get_document_or_404(document_id: UUID, session: Session) -> Document:
    document = session.scalar(
        select(Document).options(selectinload(Document.segments)).where(Document.id == document_id)
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        )

    return document


def _read_segments(document: Document) -> list[SegmentRead]:
    return [SegmentRead.model_validate(segment) for segment in document.segments]
