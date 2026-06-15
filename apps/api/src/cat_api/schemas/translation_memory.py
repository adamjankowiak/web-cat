from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
