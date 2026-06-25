import type { DocumentRead, SegmentRead } from "./api-client";

/** The document + segment the editor is currently focused on, plus its draft text. */
export type ActiveSegmentContext = {
  document: DocumentRead;
  segment: SegmentRead;
  targetText: string;
};

export type SuggestionMode = "replace" | "append" | "range";

/** A suggestion (TM entry, glossary term, or spellcheck fix) applied to a segment's target. */
export type AppliedSuggestion = {
  segmentId: string;
  targetText: string;
  appliedAt: number;
  mode?: SuggestionMode;
  start?: number;
  end?: number;
};
