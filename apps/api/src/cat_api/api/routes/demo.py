import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.schemas.demo import DemoSeedResponse
from cat_api.schemas.document import DocumentDetailRead, DocumentRead, SegmentRead
from cat_api.services.demo_seed import seed_demo_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed", response_model=DemoSeedResponse, status_code=status.HTTP_201_CREATED)
def seed_demo(session: Session = Depends(get_session)) -> DemoSeedResponse:
    try:
        result = seed_demo_data(session)
    except FileNotFoundError as exc:
        # Log the resolved server path for operators, but never echo the
        # filesystem layout back to the client.
        logger.error("Demo seed failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo sample data is unavailable on the server.",
        ) from exc

    return DemoSeedResponse(
        document=DocumentDetailRead(
            document=DocumentRead.model_validate(result.document),
            segments=[SegmentRead.model_validate(segment) for segment in result.document.segments],
        ),
        translation_memory_count=result.translation_memory_count,
        glossary_count=result.glossary_count,
    )
