from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class SegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    position: int
    source_text: str
    target_text: str | None = None
    status: str
    locked: bool
    created_at: datetime
    updated_at: datetime
