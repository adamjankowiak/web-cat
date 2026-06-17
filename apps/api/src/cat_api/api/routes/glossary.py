from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.models.glossary import GlossaryTerm
from cat_api.schemas.glossary import (
    GlossaryImportResponse,
    GlossarySearchRequest,
    GlossarySearchResponse,
    GlossaryTermCreateRequest,
    GlossaryTermRead,
    GlossaryTermUpdateRequest,
)
from cat_api.services.glossary import (
    create_glossary_term,
    import_glossary_csv,
    list_glossary_terms,
    search_glossary_terms,
    update_glossary_term,
)

router = APIRouter(prefix="/glossary", tags=["glossary"])


@router.post("/search", response_model=GlossarySearchResponse)
def search_terms(
    payload: GlossarySearchRequest,
    session: Session = Depends(get_session),
) -> GlossarySearchResponse:
    matches = search_glossary_terms(
        session,
        source_language=payload.source_language,
        target_language=payload.target_language,
        source_text=payload.source_text,
        domain=payload.domain,
        project_id=payload.project_id,
    )
    return GlossarySearchResponse(matches=matches)


@router.post("/terms", response_model=GlossaryTermRead, status_code=status.HTTP_201_CREATED)
def create_term(
    payload: GlossaryTermCreateRequest,
    session: Session = Depends(get_session),
) -> GlossaryTerm:
    term = create_glossary_term(session, payload)
    session.commit()
    session.refresh(term)
    return term


@router.get("/terms", response_model=list[GlossaryTermRead])
def list_terms(
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
    session: Session = Depends(get_session),
) -> list[GlossaryTerm]:
    return list_glossary_terms(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    )


@router.patch("/terms/{term_id}", response_model=GlossaryTermRead)
def patch_term(
    term_id: UUID,
    payload: GlossaryTermUpdateRequest,
    session: Session = Depends(get_session),
) -> GlossaryTerm:
    term = session.get(GlossaryTerm, term_id)

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Glossary term was not found.",
        )

    update_glossary_term(term, payload)
    session.commit()
    session.refresh(term)
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term(
    term_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    term = session.get(GlossaryTerm, term_id)

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Glossary term was not found.",
        )

    session.delete(term)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/import-csv",
    response_model=GlossaryImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_csv(
    csv_content: str = Body(media_type="text/csv"),
    session: Session = Depends(get_session),
) -> GlossaryImportResponse:
    try:
        terms = import_glossary_csv(session, csv_content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    session.commit()

    for term in terms:
        session.refresh(term)

    return GlossaryImportResponse(
        imported_count=len(terms),
        terms=[GlossaryTermRead.model_validate(term) for term in terms],
    )
