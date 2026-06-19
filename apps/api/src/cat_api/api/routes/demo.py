from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.schemas.demo import DemoSeedResponse
from cat_api.schemas.document import DocumentDetailRead, DocumentRead, SegmentRead
from cat_api.services.demo_seed import seed_demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed", response_model=DemoSeedResponse, status_code=status.HTTP_201_CREATED)
def seed_demo(session: Session = Depends(get_session)) -> DemoSeedResponse:
    try:
        result = seed_demo_data(session)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return DemoSeedResponse(
        document=DocumentDetailRead(
            document=DocumentRead.model_validate(result.document),
            segments=[SegmentRead.model_validate(segment) for segment in result.document.segments],
        ),
        translation_memory_count=result.translation_memory_count,
        glossary_count=result.glossary_count,
    )
