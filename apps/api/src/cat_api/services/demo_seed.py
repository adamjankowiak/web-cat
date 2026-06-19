from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cat_api.models.document import Document, Project, Segment
from cat_api.services.import_export import import_tbx, import_tmx
from cat_api.services.segmentation import segment_text

DEMO_PROJECT_NAME = "MVP Demo"
DEMO_DOMAIN = "software"
DEMO_SOURCE_LANGUAGE = "en"
DEMO_TARGET_LANGUAGE = "pl"
DEMO_DOCUMENT_FILENAME = "software-cat-source.txt"


@dataclass(frozen=True)
class DemoSeedResult:
    document: Document
    translation_memory_count: int
    glossary_count: int


def seed_demo_data(session: Session, sample_root: Path | None = None) -> DemoSeedResult:
    samples = sample_root or _default_sample_root()
    document_content = _read_sample(samples / "documents" / DEMO_DOCUMENT_FILENAME)
    tmx_content = _read_sample(samples / "translation-memory" / "software-cat-memory.tmx")
    tbx_content = _read_sample(samples / "glossaries" / "software-cat-glossary.tbx")

    project = _get_or_create_demo_project(session)
    document = _get_or_create_demo_document(session, project, document_content)
    translation_memory = import_tmx(session, tmx_content)
    glossary_terms = import_tbx(session, tbx_content)
    session.commit()

    document = _load_document(session, document.id)
    return DemoSeedResult(
        document=document,
        translation_memory_count=translation_memory.imported_count,
        glossary_count=len(glossary_terms),
    )


def _default_sample_root() -> Path:
    return Path(__file__).resolve().parents[5] / "data" / "samples"


def _read_sample(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Demo sample file was not found: {path}")

    return path.read_text(encoding="utf-8")


def _get_or_create_demo_project(session: Session) -> Project:
    project = session.scalar(
        select(Project).where(
            Project.name == DEMO_PROJECT_NAME,
            Project.source_language == DEMO_SOURCE_LANGUAGE,
            Project.target_language == DEMO_TARGET_LANGUAGE,
            Project.domain == DEMO_DOMAIN,
        )
    )

    if project is not None:
        return project

    project = Project(
        name=DEMO_PROJECT_NAME,
        source_language=DEMO_SOURCE_LANGUAGE,
        target_language=DEMO_TARGET_LANGUAGE,
        domain=DEMO_DOMAIN,
    )
    session.add(project)
    session.flush()
    return project


def _get_or_create_demo_document(
    session: Session,
    project: Project,
    document_content: str,
) -> Document:
    document = session.scalar(
        select(Document)
        .options(selectinload(Document.segments))
        .where(
            Document.project_id == project.id,
            Document.filename == DEMO_DOCUMENT_FILENAME,
        )
    )

    if document is not None:
        return document

    document = Document(
        project=project,
        filename=DEMO_DOCUMENT_FILENAME,
        source_language=DEMO_SOURCE_LANGUAGE,
        target_language=DEMO_TARGET_LANGUAGE,
        status="imported",
    )
    document.segments = [
        Segment(position=index, source_text=source_text, status="new")
        for index, source_text in enumerate(segment_text(document_content), start=1)
    ]
    session.add(document)
    session.flush()
    return document


def _load_document(session: Session, document_id: object) -> Document:
    document = session.scalar(
        select(Document).options(selectinload(Document.segments)).where(Document.id == document_id)
    )

    if document is None:
        raise RuntimeError("Seeded demo document could not be loaded.")

    return document
