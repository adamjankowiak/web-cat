from __future__ import annotations

import re
from typing import Literal

SegmentationStrategy = Literal["sentence", "paragraph"]

_BLANK_LINE_RE = re.compile(r"\n\s*\n+")
_WHITESPACE_RE = re.compile(r"\s+")
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


def segment_text(text: str, strategy: SegmentationStrategy = "sentence") -> list[str]:
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not normalized_text:
        return []

    paragraphs = [
        _normalize_segment(paragraph)
        for paragraph in _BLANK_LINE_RE.split(normalized_text)
        if _normalize_segment(paragraph)
    ]

    if strategy == "paragraph":
        return paragraphs

    segments: list[str] = []

    for paragraph in paragraphs:
        sentence_candidates = _SENTENCE_BOUNDARY_RE.split(paragraph)
        for sentence in sentence_candidates:
            segment = _normalize_segment(sentence)
            if segment:
                segments.append(segment)

    return segments


def _normalize_segment(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()
