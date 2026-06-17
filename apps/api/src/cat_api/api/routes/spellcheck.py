from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.models.spellcheck import SpellcheckIgnore
from cat_api.schemas.spellcheck import (
    SpellcheckIgnoreCreateRequest,
    SpellcheckIgnoreRead,
    SpellcheckRequest,
    SpellcheckResponse,
)
from cat_api.services.spellcheck import check_spelling, list_ignored_words, save_ignored_word

router = APIRouter(prefix="/spellcheck", tags=["spellcheck"])


@router.post("", response_model=SpellcheckResponse)
def check_text(
    payload: SpellcheckRequest,
    session: Session = Depends(get_session),
) -> SpellcheckResponse:
    try:
        issues = check_spelling(
            session,
            language=payload.language,
            text=payload.text,
            project_id=payload.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SpellcheckResponse(issues=issues)


@router.post(
    "/ignore",
    response_model=SpellcheckIgnoreRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ignore(
    payload: SpellcheckIgnoreCreateRequest,
    session: Session = Depends(get_session),
) -> SpellcheckIgnore:
    try:
        ignored_word = save_ignored_word(
            session,
            project_id=payload.project_id,
            language=payload.language,
            word=payload.word,
            created_by=payload.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    session.commit()
    session.refresh(ignored_word)
    return ignored_word


@router.get("/ignore", response_model=list[SpellcheckIgnoreRead])
def list_ignore(
    project_id: UUID,
    language: str | None = None,
    session: Session = Depends(get_session),
) -> list[SpellcheckIgnore]:
    try:
        return list_ignored_words(session, project_id=project_id, language=language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/ignore/{ignore_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ignore(
    ignore_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    ignored_word = session.get(SpellcheckIgnore, ignore_id)

    if ignored_word is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spellcheck ignored word was not found.",
        )

    session.delete(ignored_word)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
