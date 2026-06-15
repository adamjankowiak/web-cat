from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.models.document import Segment
from cat_api.schemas.document import SegmentRead, SegmentUpdateRequest

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
