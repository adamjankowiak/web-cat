from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
