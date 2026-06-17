from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TranslationMemoryMatchType = Literal["exact", "fuzzy"]


class TranslationMemoryEntryCreateRequest(BaseModel):
    source_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)
    source_text: str = Field(min_length=1)
    target_text: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=128)
    project_id: UUID | None = None
    created_by: UUID | None = None


class TranslationMemorySearchRequest(BaseModel):
    source_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)
    source_text: str = Field(min_length=1)
    domain: str | None = Field(default=None, max_length=128)
    project_id: UUID | None = None
    limit: int = Field(default=5, ge=1, le=20)
    min_score: int = Field(default=60, ge=0, le=100)


class TranslationMemoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_language: str
    target_language: str
    source_text: str
    target_text: str
    normalized_source_text: str
    domain: str | None = None
    project_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime


class TranslationMemorySuggestion(BaseModel):
    entry: TranslationMemoryEntryRead
    score: int
    match_type: TranslationMemoryMatchType


class TranslationMemorySearchResponse(BaseModel):
    suggestions: list[TranslationMemorySuggestion]


class TranslationMemoryImportResponse(BaseModel):
    imported_count: int
    entries: list[TranslationMemoryEntryRead]
