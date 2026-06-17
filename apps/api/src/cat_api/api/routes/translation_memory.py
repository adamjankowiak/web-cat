from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from cat_api.db.session import get_session
from cat_api.models.translation_memory import TranslationMemoryEntry
from cat_api.schemas.translation_memory import (
    TranslationMemoryEntryCreateRequest,
    TranslationMemoryEntryRead,
    TranslationMemoryImportResponse,
    TranslationMemorySearchRequest,
    TranslationMemorySearchResponse,
)
from cat_api.services.import_export import export_tmx, import_tmx
from cat_api.services.translation_memory import (
    list_translation_memory_entries,
    save_translation_memory_entry,
    search_translation_memory,
)

router = APIRouter(prefix="/translation-memory", tags=["translation-memory"])


@router.post("/search", response_model=TranslationMemorySearchResponse)
def search_entries(
    payload: TranslationMemorySearchRequest,
    session: Session = Depends(get_session),
) -> TranslationMemorySearchResponse:
    suggestions = search_translation_memory(
        session,
        source_language=payload.source_language,
        target_language=payload.target_language,
        source_text=payload.source_text,
        domain=payload.domain,
        project_id=payload.project_id,
        limit=payload.limit,
        min_score=payload.min_score,
    )
    return TranslationMemorySearchResponse(suggestions=suggestions)


@router.post(
    "/entries",
    response_model=TranslationMemoryEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entry(
    payload: TranslationMemoryEntryCreateRequest,
    session: Session = Depends(get_session),
) -> TranslationMemoryEntry:
    entry = save_translation_memory_entry(
        session,
        source_language=payload.source_language,
        target_language=payload.target_language,
        source_text=payload.source_text,
        target_text=payload.target_text,
        domain=payload.domain,
        project_id=payload.project_id,
        created_by=payload.created_by,
    )
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/entries", response_model=list[TranslationMemoryEntryRead])
def list_entries(
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
    session: Session = Depends(get_session),
) -> list[TranslationMemoryEntry]:
    return list_translation_memory_entries(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    )


@router.get("/export.tmx")
def export_tmx_entries(
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
    session: Session = Depends(get_session),
) -> Response:
    return Response(
        content=export_tmx(
            session,
            source_language=source_language,
            target_language=target_language,
            domain=domain,
            project_id=project_id,
        ),
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="translation-memory.tmx"'},
    )


@router.post(
    "/import-tmx",
    response_model=TranslationMemoryImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_tmx_entries(
    tmx_content: str = Body(media_type="application/xml"),
    session: Session = Depends(get_session),
) -> TranslationMemoryImportResponse:
    try:
        result = import_tmx(session, tmx_content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    session.commit()

    for entry in result.entries:
        session.refresh(entry)

    return TranslationMemoryImportResponse(
        imported_count=result.imported_count,
        entries=[TranslationMemoryEntryRead.model_validate(entry) for entry in result.entries],
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    entry = session.get(TranslationMemoryEntry, entry_id)

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation memory entry was not found.",
        )

    session.delete(entry)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
