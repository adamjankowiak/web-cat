from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SegmentStatus = Literal["new", "draft", "translated", "reviewed", "approved"]
SegmentationStrategy = Literal["sentence", "paragraph"]


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_language: str
    target_language: str
    domain: str | None = None
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    filename: str
    source_language: str
    target_language: str
    status: str
    created_at: datetime


class DocumentImportRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_language: str = Field(default="en", min_length=2, max_length=16)
    target_language: str = Field(default="pl", min_length=2, max_length=16)
    project_id: UUID | None = None
    project_name: str | None = Field(default=None, max_length=200)
    segmentation_strategy: SegmentationStrategy = "sentence"


class SegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    position: int
    source_text: str
    target_text: str | None = None
    status: SegmentStatus
    locked: bool
    created_at: datetime
    updated_at: datetime


class DocumentDetailRead(BaseModel):
    document: DocumentRead
    segments: list[SegmentRead]


class SegmentUpdateRequest(BaseModel):
    target_text: str | None = None
    status: SegmentStatus | None = None
