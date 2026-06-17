from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SpellcheckRequest(BaseModel):
    language: str = Field(min_length=2, max_length=16)
    text: str = Field(min_length=1)
    project_id: UUID | None = None
    created_by: UUID | None = None

    @field_validator("text")
    @classmethod
    def validate_text_has_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text cannot be blank.")
        return value


class SpellcheckSuggestion(BaseModel):
    value: str


class SpellcheckIssue(BaseModel):
    start: int
    end: int
    token: str
    message: str
    suggestions: list[SpellcheckSuggestion]
    rule_code: str
    language: str


class SpellcheckResponse(BaseModel):
    issues: list[SpellcheckIssue]


class SpellcheckIgnoreCreateRequest(BaseModel):
    project_id: UUID
    language: str = Field(min_length=2, max_length=16)
    word: str = Field(min_length=1, max_length=255)
    created_by: UUID | None = None

    @field_validator("word")
    @classmethod
    def validate_word_has_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Word cannot be blank.")
        return value


class SpellcheckIgnoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    language: str
    word: str
    created_by: UUID | None = None
    created_at: datetime
