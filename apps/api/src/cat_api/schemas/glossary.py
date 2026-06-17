from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GlossaryTermCreateRequest(BaseModel):
    project_id: UUID | None = None
    source_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)
    source_term: str = Field(min_length=1, max_length=255)
    target_term: str = Field(min_length=1, max_length=255)
    definition: str | None = None
    domain: str | None = Field(default=None, max_length=128)
    case_sensitive: bool = False
    forbidden: bool = False
    example_source: str | None = None
    example_target: str | None = None


class GlossaryTermUpdateRequest(BaseModel):
    project_id: UUID | None = None
    source_language: str | None = Field(default=None, min_length=2, max_length=16)
    target_language: str | None = Field(default=None, min_length=2, max_length=16)
    source_term: str | None = Field(default=None, min_length=1, max_length=255)
    target_term: str | None = Field(default=None, min_length=1, max_length=255)
    definition: str | None = None
    domain: str | None = Field(default=None, max_length=128)
    case_sensitive: bool | None = None
    forbidden: bool | None = None
    example_source: str | None = None
    example_target: str | None = None


class GlossarySearchRequest(BaseModel):
    source_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)
    source_text: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=128)
    project_id: UUID | None = None


class GlossaryTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None = None
    source_language: str
    target_language: str
    source_term: str
    target_term: str
    definition: str | None = None
    domain: str | None = None
    case_sensitive: bool
    forbidden: bool
    example_source: str | None = None
    example_target: str | None = None


class GlossaryTermMatch(BaseModel):
    term: GlossaryTermRead
    start: int
    end: int
    matched_text: str


class GlossarySearchResponse(BaseModel):
    matches: list[GlossaryTermMatch]


class GlossaryImportResponse(BaseModel):
    imported_count: int
    terms: list[GlossaryTermRead]


class TerminologyViolation(BaseModel):
    term: GlossaryTermRead
    violation_type: str
    message: str
    start: int
    end: int
    matched_text: str


class TerminologyValidationError(BaseModel):
    violations: list[TerminologyViolation]
