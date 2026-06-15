"""Create base CAT data model.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("source_language", sa.String(length=16), nullable=False),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_language", sa.String(length=16), nullable=False),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="new", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])

    op.create_table(
        "segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="new", nullable=False),
        sa.Column("locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "position", name="uq_segments_document_position"),
    )
    op.create_index("ix_segments_document_id", "segments", ["document_id"])

    op.create_table(
        "translation_memory_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_language", sa.String(length=16), nullable=False),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("normalized_source_text", sa.String(length=2048), nullable=False),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tme_language_pair",
        "translation_memory_entries",
        ["source_language", "target_language", "domain"],
    )
    op.create_index(
        "ix_tme_normalized_source_text",
        "translation_memory_entries",
        ["normalized_source_text"],
    )
    op.create_index("ix_tme_project_id", "translation_memory_entries", ["project_id"])
    op.execute(
        "CREATE INDEX ix_tme_normalized_source_trgm "
        "ON translation_memory_entries USING gin (normalized_source_text gin_trgm_ops)"
    )

    op.create_table(
        "glossary_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_language", sa.String(length=16), nullable=False),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("source_term", sa.String(length=255), nullable=False),
        sa.Column("target_term", sa.String(length=255), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("case_sensitive", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("forbidden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("example_source", sa.Text(), nullable=True),
        sa.Column("example_target", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_glossary_terms_project_id", "glossary_terms", ["project_id"])
    op.create_index(
        "ix_glossary_terms_language_pair",
        "glossary_terms",
        ["source_language", "target_language", "domain"],
    )

    op.create_table(
        "spellcheck_ignores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "language", "word", name="uq_spellcheck_ignore_word"),
    )
    op.create_index("ix_spellcheck_ignores_project_id", "spellcheck_ignores", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_spellcheck_ignores_project_id", table_name="spellcheck_ignores")
    op.drop_table("spellcheck_ignores")
    op.drop_index("ix_glossary_terms_language_pair", table_name="glossary_terms")
    op.drop_index("ix_glossary_terms_project_id", table_name="glossary_terms")
    op.drop_table("glossary_terms")
    op.execute("DROP INDEX IF EXISTS ix_tme_normalized_source_trgm")
    op.drop_index("ix_tme_project_id", table_name="translation_memory_entries")
    op.drop_index("ix_tme_normalized_source_text", table_name="translation_memory_entries")
    op.drop_index("ix_tme_language_pair", table_name="translation_memory_entries")
    op.drop_table("translation_memory_entries")
    op.drop_index("ix_segments_document_id", table_name="segments")
    op.drop_table("segments")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_table("documents")
    op.drop_table("projects")
    op.drop_table("users")
