from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from cat_api.models.translation_memory import TranslationMemoryEntry
from cat_api.schemas.translation_memory import (
    TranslationMemoryEntryRead,
    TranslationMemorySuggestion,
)

_WHITESPACE_RE = re.compile(r"\s+")
_TYPOGRAPHIC_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
)


def normalize_source_text(source_text: str) -> str:
    normalized = unicodedata.normalize("NFKC", source_text)
    normalized = normalized.translate(_TYPOGRAPHIC_TRANSLATION)
    normalized = _WHITESPACE_RE.sub(" ", normalized.strip())
    return normalized.casefold()


def save_translation_memory_entry(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    source_text: str,
    target_text: str,
    domain: str | None = None,
    project_id: UUID | None = None,
    created_by: UUID | None = None,
) -> TranslationMemoryEntry:
    normalized_source_text = normalize_source_text(source_text)
    cleaned_target_text = target_text.strip()

    existing_entry = session.scalar(
        select(TranslationMemoryEntry).where(
            TranslationMemoryEntry.source_language == source_language,
            TranslationMemoryEntry.target_language == target_language,
            TranslationMemoryEntry.normalized_source_text == normalized_source_text,
            TranslationMemoryEntry.target_text == cleaned_target_text,
            TranslationMemoryEntry.project_id == project_id,
            TranslationMemoryEntry.domain == domain,
        )
    )

    if existing_entry is not None:
        return existing_entry

    entry = TranslationMemoryEntry(
        source_language=source_language,
        target_language=target_language,
        source_text=source_text.strip(),
        target_text=cleaned_target_text,
        normalized_source_text=normalized_source_text,
        domain=domain,
        project_id=project_id,
        created_by=created_by,
    )
    session.add(entry)
    session.flush()
    return entry


def search_translation_memory(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    source_text: str,
    domain: str | None = None,
    project_id: UUID | None = None,
    limit: int = 5,
    min_score: int = 60,
) -> list[TranslationMemorySuggestion]:
    normalized_query = normalize_source_text(source_text)
    entries = _candidate_entries(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    )
    suggestions: list[TranslationMemorySuggestion] = []

    for entry in entries:
        if entry.normalized_source_text == normalized_query:
            score = 100
            match_type = "exact"
        else:
            score = round(fuzz.ratio(normalized_query, entry.normalized_source_text))
            match_type = "fuzzy"

        if score >= min_score:
            suggestions.append(
                TranslationMemorySuggestion(
                    entry=TranslationMemoryEntryRead.model_validate(entry),
                    score=score,
                    match_type=match_type,
                )
            )

    suggestions.sort(
        key=lambda suggestion: (
            suggestion.score,
            suggestion.match_type == "exact",
            suggestion.entry.created_at,
        ),
        reverse=True,
    )
    return suggestions[:limit]


def list_translation_memory_entries(
    session: Session,
    *,
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> list[TranslationMemoryEntry]:
    statement = select(TranslationMemoryEntry)

    if source_language is not None:
        statement = statement.where(TranslationMemoryEntry.source_language == source_language)

    if target_language is not None:
        statement = statement.where(TranslationMemoryEntry.target_language == target_language)

    if domain is not None:
        statement = statement.where(TranslationMemoryEntry.domain == domain)

    if project_id is not None:
        statement = statement.where(TranslationMemoryEntry.project_id == project_id)

    statement = statement.order_by(TranslationMemoryEntry.created_at.desc())
    return list(session.scalars(statement).all())


def _candidate_entries(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    domain: str | None,
    project_id: UUID | None,
) -> list[TranslationMemoryEntry]:
    statement = select(TranslationMemoryEntry).where(
        TranslationMemoryEntry.source_language == source_language,
        TranslationMemoryEntry.target_language == target_language,
    )

    if domain is not None:
        statement = statement.where(
            (TranslationMemoryEntry.domain == domain) | (TranslationMemoryEntry.domain.is_(None))
        )

    if project_id is not None:
        statement = statement.where(
            (TranslationMemoryEntry.project_id == project_id)
            | (TranslationMemoryEntry.project_id.is_(None))
        )

    return list(session.scalars(statement).all())
