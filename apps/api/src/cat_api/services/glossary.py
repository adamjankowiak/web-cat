from __future__ import annotations

import csv
import io
import re
import unicodedata
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from cat_api.models.glossary import GlossaryTerm
from cat_api.schemas.glossary import (
    GlossaryTermCreateRequest,
    GlossaryTermMatch,
    GlossaryTermRead,
    GlossaryTermUpdateRequest,
    TerminologyViolation,
)

_WHITESPACE_RE = re.compile(r"\s+")
_BOOLEAN_TRUE = {"1", "true", "yes", "y", "tak"}
_BOOLEAN_FALSE = {"0", "false", "no", "n", "nie", ""}
_REQUIRED_CSV_COLUMNS = {
    "source_term",
    "target_term",
    "source_language",
    "target_language",
}
_OPTIONAL_CSV_COLUMNS = {
    "definition",
    "domain",
    "case_sensitive",
    "forbidden",
    "example_source",
    "example_target",
    "project_id",
}


def normalize_term(term: str, *, case_sensitive: bool = False) -> str:
    normalized = unicodedata.normalize("NFKC", term)
    normalized = _WHITESPACE_RE.sub(" ", normalized.strip())
    return normalized if case_sensitive else normalized.casefold()


def create_glossary_term(
    session: Session,
    payload: GlossaryTermCreateRequest,
) -> GlossaryTerm:
    term = GlossaryTerm(**payload.model_dump())
    session.add(term)
    session.flush()
    return term


def update_glossary_term(
    term: GlossaryTerm,
    payload: GlossaryTermUpdateRequest,
) -> GlossaryTerm:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(term, field, value)

    return term


def list_glossary_terms(
    session: Session,
    *,
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> list[GlossaryTerm]:
    statement = select(GlossaryTerm)

    if source_language is not None:
        statement = statement.where(GlossaryTerm.source_language == source_language)

    if target_language is not None:
        statement = statement.where(GlossaryTerm.target_language == target_language)

    if domain is not None:
        statement = statement.where(GlossaryTerm.domain == domain)

    if project_id is not None:
        statement = statement.where(GlossaryTerm.project_id == project_id)

    statement = statement.order_by(GlossaryTerm.source_term, GlossaryTerm.target_term)
    return list(session.scalars(statement).all())


def search_glossary_terms(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    source_text: str,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> list[GlossaryTermMatch]:
    matches: list[GlossaryTermMatch] = []

    for term in _candidate_terms(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    ):
        for match in _find_term_occurrences(source_text, term.source_term, term.case_sensitive):
            matches.append(
                GlossaryTermMatch(
                    term=GlossaryTermRead.model_validate(term),
                    start=match.start(),
                    end=match.end(),
                    matched_text=match.group(0),
                )
            )

    matches.sort(key=lambda match: (match.start, -(match.end - match.start), match.term.source_term))
    return matches


def validate_terminology(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    source_text: str,
    target_text: str,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> list[TerminologyViolation]:
    violations: list[TerminologyViolation] = []
    matches = search_glossary_terms(
        session,
        source_language=source_language,
        target_language=target_language,
        source_text=source_text,
        domain=domain,
        project_id=project_id,
    )

    for match in matches:
        term = match.term
        target_matches = list(
            _find_term_occurrences(target_text, term.target_term, term.case_sensitive)
        )

        if term.forbidden and target_matches:
            violations.append(
                TerminologyViolation(
                    term=term,
                    violation_type="forbidden_present",
                    message=f"Forbidden term '{term.target_term}' is present in target text.",
                    start=match.start,
                    end=match.end,
                    matched_text=match.matched_text,
                )
            )

        if not term.forbidden and not target_matches:
            violations.append(
                TerminologyViolation(
                    term=term,
                    violation_type="missing_required",
                    message=f"Required term '{term.target_term}' is missing from target text.",
                    start=match.start,
                    end=match.end,
                    matched_text=match.matched_text,
                )
            )

    return violations


def import_glossary_csv(session: Session, csv_content: str) -> list[GlossaryTerm]:
    reader = csv.DictReader(io.StringIO(csv_content))

    if reader.fieldnames is None:
        raise ValueError("CSV header row is required.")

    fieldnames = {field.strip() for field in reader.fieldnames if field is not None}
    missing_columns = sorted(_REQUIRED_CSV_COLUMNS - fieldnames)

    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}.")

    supported_columns = _REQUIRED_CSV_COLUMNS | _OPTIONAL_CSV_COLUMNS
    unsupported_columns = sorted(fieldnames - supported_columns)

    if unsupported_columns:
        raise ValueError(f"CSV contains unsupported columns: {', '.join(unsupported_columns)}.")

    terms: list[GlossaryTerm] = []
    row_errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        cleaned_row = {key.strip(): _clean_csv_value(value) for key, value in row.items() if key}
        missing_values = [
            column for column in sorted(_REQUIRED_CSV_COLUMNS) if not cleaned_row.get(column)
        ]

        if missing_values:
            row_errors.append(
                f"Row {row_number} is missing values for: {', '.join(missing_values)}."
            )
            continue

        try:
            payload = GlossaryTermCreateRequest(
                source_term=cleaned_row["source_term"],
                target_term=cleaned_row["target_term"],
                source_language=cleaned_row["source_language"],
                target_language=cleaned_row["target_language"],
                definition=cleaned_row.get("definition"),
                domain=cleaned_row.get("domain"),
                case_sensitive=_parse_csv_bool(cleaned_row.get("case_sensitive"), row_number),
                forbidden=_parse_csv_bool(cleaned_row.get("forbidden"), row_number),
                example_source=cleaned_row.get("example_source"),
                example_target=cleaned_row.get("example_target"),
                project_id=UUID(cleaned_row["project_id"]) if cleaned_row.get("project_id") else None,
            )
        except ValueError as exc:
            row_errors.append(str(exc))
            continue

        terms.append(create_glossary_term(session, payload))

    if row_errors:
        raise ValueError(" ".join(row_errors))

    return terms


def _candidate_terms(
    session: Session,
    *,
    source_language: str,
    target_language: str,
    domain: str | None,
    project_id: UUID | None,
) -> list[GlossaryTerm]:
    statement = select(GlossaryTerm).where(
        GlossaryTerm.source_language == source_language,
        GlossaryTerm.target_language == target_language,
    )

    if domain is not None:
        statement = statement.where((GlossaryTerm.domain == domain) | (GlossaryTerm.domain.is_(None)))

    if project_id is not None:
        statement = statement.where(
            (GlossaryTerm.project_id == project_id) | (GlossaryTerm.project_id.is_(None))
        )

    statement = statement.order_by(GlossaryTerm.source_term)
    return list(session.scalars(statement).all())


def _find_term_occurrences(text: str, term: str, case_sensitive: bool) -> list[re.Match[str]]:
    normalized_term = normalize_term(term, case_sensitive=True)

    if not normalized_term:
        return []

    pattern = _term_pattern(normalized_term)
    flags = 0 if case_sensitive else re.IGNORECASE
    return list(re.finditer(pattern, text, flags=flags))


def _term_pattern(term: str) -> str:
    escaped_parts = [re.escape(part) for part in _WHITESPACE_RE.split(term)]
    escaped_term = r"\s+".join(escaped_parts)
    return rf"(?<!\w){escaped_term}(?!\w)"


def _clean_csv_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _parse_csv_bool(value: str | None, row_number: int) -> bool:
    if value is None:
        return False

    normalized = value.strip().casefold()

    if normalized in _BOOLEAN_TRUE:
        return True

    if normalized in _BOOLEAN_FALSE:
        return False

    raise ValueError(f"Row {row_number} has invalid boolean value: {value}.")
