from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.orm import Session

from cat_api.models.document import Document
from cat_api.models.glossary import GlossaryTerm
from cat_api.models.translation_memory import TranslationMemoryEntry
from cat_api.schemas.glossary import GlossaryTermCreateRequest
from cat_api.services.glossary import create_glossary_term, list_glossary_terms
from cat_api.services.translation_memory import (
    list_translation_memory_entries,
    save_translation_memory_entry,
)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
XLIFF_NS = "urn:oasis:names:tc:xliff:document:1.2"
ElementTree.register_namespace("", XLIFF_NS)


@dataclass(frozen=True)
class TmxImportResult:
    entries: list[TranslationMemoryEntry]

    @property
    def imported_count(self) -> int:
        return len(self.entries)


def export_document_txt(document: Document) -> str:
    return "\n".join(
        (segment.target_text.strip() if segment.target_text and segment.target_text.strip() else segment.source_text)
        for segment in sorted(document.segments, key=lambda segment: segment.position)
    )


def export_document_xliff(document: Document) -> str:
    root = ElementTree.Element(
        f"{{{XLIFF_NS}}}xliff",
        {
            "version": "1.2",
        },
    )
    file_element = ElementTree.SubElement(
        root,
        f"{{{XLIFF_NS}}}file",
        {
            "source-language": document.source_language,
            "target-language": document.target_language,
            "datatype": "plaintext",
            "original": document.filename,
        },
    )
    body = ElementTree.SubElement(file_element, f"{{{XLIFF_NS}}}body")

    for segment in sorted(document.segments, key=lambda item: item.position):
        trans_unit = ElementTree.SubElement(
            body,
            f"{{{XLIFF_NS}}}trans-unit",
            {"id": str(segment.id), "resname": str(segment.position)},
        )
        source = ElementTree.SubElement(trans_unit, f"{{{XLIFF_NS}}}source")
        source.text = segment.source_text
        target = ElementTree.SubElement(
            trans_unit,
            f"{{{XLIFF_NS}}}target",
            {"state": segment.status},
        )
        target.text = segment.target_text or ""
        note = ElementTree.SubElement(trans_unit, f"{{{XLIFF_NS}}}note", {"from": "web-cat:status"})
        note.text = segment.status

    return _xml_to_string(root)


def export_tmx(
    session: Session,
    *,
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> str:
    entries = list_translation_memory_entries(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    )
    root = ElementTree.Element("tmx", {"version": "1.4"})
    ElementTree.SubElement(
        root,
        "header",
        {
            "creationtool": "web-cat",
            "creationtoolversion": "0.1.0",
            "segtype": "sentence",
            "o-tmf": "web-cat",
            "adminlang": source_language or "en",
            "srclang": source_language or "*all*",
            "datatype": "PlainText",
        },
    )
    body = ElementTree.SubElement(root, "body")

    for entry in entries:
        tu_attributes = {"tuid": str(entry.id)}

        if entry.created_at is not None:
            tu_attributes["creationdate"] = _format_tmx_date(entry.created_at)

        tu = ElementTree.SubElement(body, "tu", tu_attributes)
        _add_optional_prop(tu, "domain", entry.domain)
        _add_optional_prop(tu, "project_id", str(entry.project_id) if entry.project_id else None)

        source_tuv = ElementTree.SubElement(tu, "tuv", {XML_LANG: entry.source_language})
        source_seg = ElementTree.SubElement(source_tuv, "seg")
        source_seg.text = entry.source_text

        target_tuv = ElementTree.SubElement(tu, "tuv", {XML_LANG: entry.target_language})
        target_seg = ElementTree.SubElement(target_tuv, "seg")
        target_seg.text = entry.target_text

    return _xml_to_string(root)


def import_tmx(session: Session, tmx_content: str) -> TmxImportResult:
    root = _parse_xml(tmx_content, "TMX")

    if _local_name(root.tag) != "tmx":
        raise ValueError("TMX root element must be <tmx>.")

    body = _find_child(root, "body")

    if body is None:
        raise ValueError("TMX body element is required.")

    entries: list[TranslationMemoryEntry] = []

    for index, tu in enumerate(_find_children(body, "tu"), start=1):
        properties = _read_props(tu)
        tuv_values = _read_tuv_segments(tu)

        if len(tuv_values) < 2:
            raise ValueError(f"TMX tu #{index} must contain at least two tuv/seg pairs.")

        source_language, source_text = tuv_values[0]
        target_language, target_text = tuv_values[1]

        if not source_text or not target_text:
            raise ValueError(f"TMX tu #{index} contains an empty source or target segment.")

        entry = save_translation_memory_entry(
            session,
            source_language=source_language,
            target_language=target_language,
            source_text=source_text,
            target_text=target_text,
            domain=properties.get("domain"),
            project_id=_parse_optional_uuid(properties.get("project_id"), f"TMX tu #{index}"),
        )
        entries.append(entry)

    if not entries:
        raise ValueError("TMX body does not contain translation units.")

    return TmxImportResult(entries=entries)


def export_tbx(
    session: Session,
    *,
    source_language: str | None = None,
    target_language: str | None = None,
    domain: str | None = None,
    project_id: UUID | None = None,
) -> str:
    terms = list_glossary_terms(
        session,
        source_language=source_language,
        target_language=target_language,
        domain=domain,
        project_id=project_id,
    )
    root = ElementTree.Element("tbx", {"style": "dca", "type": "TBX-Core"})
    ElementTree.SubElement(root, "tbxHeader")
    text = ElementTree.SubElement(root, "text")
    body = ElementTree.SubElement(text, "body")

    for term in terms:
        term_entry = ElementTree.SubElement(body, "termEntry", {"id": str(term.id)})
        _add_optional_descrip(term_entry, "domain", term.domain)
        _add_optional_descrip(term_entry, "definition", term.definition)
        _add_optional_descrip(term_entry, "project_id", str(term.project_id) if term.project_id else None)
        _add_optional_descrip(term_entry, "case_sensitive", _format_bool(term.case_sensitive))
        _add_optional_descrip(term_entry, "forbidden", _format_bool(term.forbidden))

        source_lang_set = ElementTree.SubElement(term_entry, "langSet", {XML_LANG: term.source_language})
        source_tig = ElementTree.SubElement(source_lang_set, "tig")
        source_term = ElementTree.SubElement(source_tig, "term")
        source_term.text = term.source_term

        target_lang_set = ElementTree.SubElement(term_entry, "langSet", {XML_LANG: term.target_language})
        target_tig = ElementTree.SubElement(target_lang_set, "tig")
        target_term = ElementTree.SubElement(target_tig, "term")
        target_term.text = term.target_term

    return _xml_to_string(root)


def import_tbx(session: Session, tbx_content: str) -> list[GlossaryTerm]:
    root = _parse_xml(tbx_content, "TBX")

    if _local_name(root.tag) != "tbx":
        raise ValueError("TBX root element must be <tbx>.")

    body = _find_descendant(root, "body")

    if body is None:
        raise ValueError("TBX body element is required.")

    terms: list[GlossaryTerm] = []

    for index, term_entry in enumerate(_find_children(body, "termEntry"), start=1):
        properties = _read_descrips(term_entry)
        lang_terms = _read_lang_terms(term_entry)

        if len(lang_terms) < 2:
            raise ValueError(f"TBX termEntry #{index} must contain at least two langSet/term pairs.")

        source_language, source_term = lang_terms[0]
        target_language, target_term = lang_terms[1]

        if not source_term or not target_term:
            raise ValueError(f"TBX termEntry #{index} contains an empty source or target term.")

        payload = GlossaryTermCreateRequest(
            source_language=source_language,
            target_language=target_language,
            source_term=source_term,
            target_term=target_term,
            definition=properties.get("definition"),
            domain=properties.get("domain"),
            case_sensitive=_parse_bool(properties.get("case_sensitive"), default=False),
            forbidden=_parse_bool(properties.get("forbidden"), default=False),
            project_id=_parse_optional_uuid(properties.get("project_id"), f"TBX termEntry #{index}"),
        )
        terms.append(_save_glossary_term_once(session, payload))

    if not terms:
        raise ValueError("TBX body does not contain term entries.")

    return terms


def _xml_to_string(root: ElementTree.Element) -> str:
    return ElementTree.tostring(root, encoding="unicode", xml_declaration=True)


def _parse_xml(content: str, format_name: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"{format_name} XML is invalid.") from exc


def _format_tmx_date(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def _add_optional_prop(parent: ElementTree.Element, prop_type: str, value: str | None) -> None:
    if value is None:
        return

    prop = ElementTree.SubElement(parent, "prop", {"type": prop_type})
    prop.text = value


def _add_optional_descrip(parent: ElementTree.Element, descrip_type: str, value: str | None) -> None:
    if value is None:
        return

    descrip = ElementTree.SubElement(parent, "descrip", {"type": descrip_type})
    descrip.text = value


def _read_props(parent: ElementTree.Element) -> dict[str, str]:
    return {
        prop.attrib["type"]: _element_text(prop)
        for prop in _find_children(parent, "prop")
        if prop.attrib.get("type")
    }


def _read_descrips(parent: ElementTree.Element) -> dict[str, str]:
    return {
        descrip.attrib["type"]: _element_text(descrip)
        for descrip in _find_children(parent, "descrip")
        if descrip.attrib.get("type")
    }


def _read_tuv_segments(tu: ElementTree.Element) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []

    for tuv in _find_children(tu, "tuv"):
        language = tuv.attrib.get(XML_LANG)
        seg = _find_child(tuv, "seg")

        if language is None or seg is None:
            continue

        values.append((language, _element_text(seg)))

    return values


def _read_lang_terms(term_entry: ElementTree.Element) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []

    for lang_set in _find_children(term_entry, "langSet"):
        language = lang_set.attrib.get(XML_LANG)
        term = _find_descendant(lang_set, "term")

        if language is None or term is None:
            continue

        values.append((language, _element_text(term)))

    return values


def _save_glossary_term_once(
    session: Session,
    payload: GlossaryTermCreateRequest,
) -> GlossaryTerm:
    existing = session.scalar(
        select(GlossaryTerm).where(
            GlossaryTerm.project_id == payload.project_id,
            GlossaryTerm.source_language == payload.source_language,
            GlossaryTerm.target_language == payload.target_language,
            GlossaryTerm.source_term == payload.source_term,
            GlossaryTerm.target_term == payload.target_term,
            GlossaryTerm.definition == payload.definition,
            GlossaryTerm.domain == payload.domain,
            GlossaryTerm.case_sensitive == payload.case_sensitive,
            GlossaryTerm.forbidden == payload.forbidden,
        )
    )

    if existing is not None:
        return existing

    return create_glossary_term(session, payload)


def _find_child(parent: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((child for child in parent if _local_name(child.tag) == name), None)


def _find_children(parent: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in parent if _local_name(child.tag) == name]


def _find_descendant(parent: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((element for element in parent.iter() if _local_name(element.tag) == name), None)


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[1]

    return tag


def _element_text(element: ElementTree.Element) -> str:
    return "".join(element.itertext()).strip()


def _parse_optional_uuid(value: str | None, context: str) -> UUID | None:
    if not value:
        return None

    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"{context} has invalid project_id.") from exc


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().casefold()

    if normalized in {"1", "true", "yes", "y", "tak"}:
        return True

    if normalized in {"0", "false", "no", "n", "nie", ""}:
        return False

    raise ValueError(f"Invalid boolean value: {value}.")
