from pydantic import BaseModel

from cat_api.schemas.document import DocumentDetailRead


class DemoSeedResponse(BaseModel):
    document: DocumentDetailRead
    translation_memory_count: int
    glossary_count: int
