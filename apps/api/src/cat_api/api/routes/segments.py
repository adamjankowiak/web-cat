from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cat_api.db.session import get_session
from cat_api.models.document import Document, Segment
from cat_api.schemas.document import SegmentRead, SegmentUpdateRequest
from cat_api.schemas.glossary import TerminologyValidationError
from cat_api.services.glossary import validate_terminology
from cat_api.services.translation_memory import save_translation_memory_entry

router = APIRouter(prefix="/segments", tags=["segments"])


@router.patch("/{segment_id}", response_model=SegmentRead)
def update_segment(
    segment_id: UUID,
    payload: SegmentUpdateRequest,
    session: Session = Depends(get_session),
) -> Segment:
    segment = session.get(Segment, segment_id)

    if segment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment was not found.",
        )

    if segment.locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Locked segment cannot be edited.",
        )

    if payload.target_text is not None:
        segment.target_text = payload.target_text

        if payload.status is None:
            segment.status = "draft" if payload.target_text.strip() else "new"

    if payload.status is not None:
        segment.status = payload.status

    session.commit()
    session.refresh(segment)

    return segment


@router.post("/{segment_id}/approve", response_model=SegmentRead)
def approve_segment(
    segment_id: UUID,
    session: Session = Depends(get_session),
) -> Segment:
    segment = session.scalar(
        select(Segment)
        .options(selectinload(Segment.document).selectinload(Document.project))
        .where(Segment.id == segment_id)
    )

    if segment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment was not found.",
        )

    if segment.locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Locked segment cannot be approved.",
        )

    if segment.target_text is None or not segment.target_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Segment cannot be approved without target text.",
        )

    violations = validate_terminology(
        session,
        source_language=segment.document.source_language,
        target_language=segment.document.target_language,
        source_text=segment.source_text,
        target_text=segment.target_text,
        domain=segment.document.project.domain,
        project_id=segment.document.project_id,
    )

    if violations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=TerminologyValidationError(violations=violations).model_dump(mode="json"),
        )

    segment.status = "approved"
    save_translation_memory_entry(
        session,
        source_language=segment.document.source_language,
        target_language=segment.document.target_language,
        source_text=segment.source_text,
        target_text=segment.target_text,
        domain=segment.document.project.domain,
        project_id=segment.document.project_id,
    )
    session.commit()
    session.refresh(segment)
    return segment
