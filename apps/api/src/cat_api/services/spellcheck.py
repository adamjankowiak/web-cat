from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from cat_api.models.spellcheck import SpellcheckIgnore
from cat_api.schemas.spellcheck import SpellcheckIssue, SpellcheckSuggestion

_TOKEN_RE = re.compile(
    r"[0-9A-Za-zÀ-ÖØ-öø-ÿĄĆĘŁŃÓŚŹŻąćęłńóśźżÄÖÜäöüẞß]+"
    r"(?:[-'][0-9A-Za-zÀ-ÖØ-öø-ÿĄĆĘŁŃÓŚŹŻąćęłńóśźżÄÖÜäöüẞß]+)?",
)

_SUPPORTED_LANGUAGES = {"pl", "en", "de"}

_DICTIONARIES: dict[str, set[str]] = {
    "pl": {
        "aktywny",
        "aplikacja",
        "automatycznie",
        "blad",
        "błąd",
        "docelowe",
        "dokument",
        "edytor",
        "jest",
        "okno",
        "panel",
        "plik",
        "poprawne",
        "segment",
        "slowo",
        "słowo",
        "tekst",
        "tlumaczenie",
        "tłumaczenie",
        "to",
        "zapisz",
        "zamknij",
    },
    "en": {
        "active",
        "application",
        "automatically",
        "close",
        "document",
        "editor",
        "file",
        "is",
        "memory",
        "panel",
        "save",
        "saved",
        "segment",
        "spellcheck",
        "target",
        "text",
        "the",
        "this",
        "translation",
        "window",
    },
    "de": {
        "datei",
        "der",
        "die",
        "dies",
        "dokument",
        "fenster",
        "ist",
        "segment",
        "sie",
        "speichern",
        "text",
        "ubersetzung",
        "übersetzung",
        "zieltext",
    },
}


@dataclass(frozen=True)
class TokenMatch:
    token: str
    start: int
    end: int


def normalize_language(language: str) -> str:
    normalized = language.strip().casefold().split("-", maxsplit=1)[0].split("_", maxsplit=1)[0]

    if normalized not in _SUPPORTED_LANGUAGES:
        raise ValueError(f"Spellcheck language is not supported: {language}.")

    return normalized


def normalize_word(word: str) -> str:
    normalized = unicodedata.normalize("NFKC", word)
    return normalized.strip().casefold()


def check_spelling(
    session: Session,
    *,
    language: str,
    text: str,
    project_id: UUID | None = None,
) -> list[SpellcheckIssue]:
    normalized_language = normalize_language(language)
    dictionary = _DICTIONARIES[normalized_language]
    ignored_words = _ignored_words(session, language=normalized_language, project_id=project_id)
    issues: list[SpellcheckIssue] = []

    for match in _tokenize(text):
        normalized_token = normalize_word(match.token)

        if _should_skip_token(normalized_token, dictionary, ignored_words):
            continue

        issues.append(
            SpellcheckIssue(
                start=match.start,
                end=match.end,
                token=match.token,
                message=f"Unknown word '{match.token}' for language '{normalized_language}'.",
                suggestions=[
                    SpellcheckSuggestion(value=suggestion)
                    for suggestion in _suggest_words(normalized_token, dictionary)
                ],
                rule_code="LOCAL_DICTIONARY_UNKNOWN_WORD",
                language=normalized_language,
            )
        )

    return issues


def list_ignored_words(
    session: Session,
    *,
    project_id: UUID,
    language: str | None = None,
) -> list[SpellcheckIgnore]:
    statement = select(SpellcheckIgnore).where(SpellcheckIgnore.project_id == project_id)

    if language is not None:
        statement = statement.where(SpellcheckIgnore.language == normalize_language(language))

    statement = statement.order_by(SpellcheckIgnore.language, SpellcheckIgnore.word)
    return list(session.scalars(statement).all())


def save_ignored_word(
    session: Session,
    *,
    project_id: UUID,
    language: str,
    word: str,
    created_by: UUID | None = None,
) -> SpellcheckIgnore:
    normalized_language = normalize_language(language)
    normalized_word = normalize_word(word)

    existing = session.scalar(
        select(SpellcheckIgnore).where(
            SpellcheckIgnore.project_id == project_id,
            SpellcheckIgnore.language == normalized_language,
            SpellcheckIgnore.word == normalized_word,
        )
    )

    if existing is not None:
        return existing

    ignored_word = SpellcheckIgnore(
        project_id=project_id,
        language=normalized_language,
        word=normalized_word,
        created_by=created_by,
    )
    session.add(ignored_word)
    session.flush()
    return ignored_word


def _tokenize(text: str) -> list[TokenMatch]:
    return [
        TokenMatch(token=match.group(0), start=match.start(), end=match.end())
        for match in _TOKEN_RE.finditer(text)
    ]


def _ignored_words(
    session: Session,
    *,
    language: str,
    project_id: UUID | None,
) -> set[str]:
    if project_id is None:
        return set()

    statement = select(SpellcheckIgnore.word).where(
        SpellcheckIgnore.project_id == project_id,
        SpellcheckIgnore.language == language,
    )
    return set(session.scalars(statement).all())


def _should_skip_token(token: str, dictionary: set[str], ignored_words: set[str]) -> bool:
    return (
        not token
        or token in dictionary
        or token in ignored_words
        or any(character.isdigit() for character in token)
        or len(token) == 1
    )


def _suggest_words(token: str, dictionary: set[str]) -> list[str]:
    matches = process.extract(
        token,
        sorted(dictionary),
        scorer=fuzz.WRatio,
        limit=3,
        score_cutoff=70,
    )
    return [word for word, _score, _index in matches]
