from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from cat_api.db.session import Base


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_language: Mapped[str] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str] = mapped_column(String(16), nullable=False)
    source_term: Mapped[str] = mapped_column(String(255), nullable=False)
    target_term: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    forbidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    example_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_target: Mapped[str | None] = mapped_column(Text, nullable=True)
