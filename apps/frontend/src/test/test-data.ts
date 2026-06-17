import type {
  DocumentDetailRead,
  DocumentRead,
  GlossaryTermMatch,
  SegmentRead,
  SpellcheckIssue,
  TranslationMemorySuggestion
} from "../lib/api-client";

export const documentRead: DocumentRead = {
  id: "document-1",
  project_id: "project-1",
  filename: "demo.txt",
  source_language: "en",
  target_language: "pl",
  status: "imported",
  created_at: "2026-06-17T10:00:00Z"
};

export const segments: SegmentRead[] = [
  {
    id: "segment-1",
    document_id: "document-1",
    position: 1,
    source_text: "Save the file.",
    target_text: "",
    status: "new",
    locked: false,
    created_at: "2026-06-17T10:00:00Z",
    updated_at: "2026-06-17T10:00:00Z"
  },
  {
    id: "segment-2",
    document_id: "document-1",
    position: 2,
    source_text: "Close the window.",
    target_text: "Zamknij okno.",
    status: "draft",
    locked: false,
    created_at: "2026-06-17T10:00:00Z",
    updated_at: "2026-06-17T10:00:00Z"
  }
];

export const documentDetail: DocumentDetailRead = {
  document: documentRead,
  segments
};

export const memorySuggestion: TranslationMemorySuggestion = {
  score: 96,
  match_type: "fuzzy",
  entry: {
    id: "tm-1",
    source_language: "en",
    target_language: "pl",
    source_text: "Save the file before closing the window.",
    target_text: "Zapisz plik przed zamknieciem okna.",
    normalized_source_text: "save the file before closing the window.",
    domain: "software",
    project_id: "project-1",
    created_by: null,
    created_at: "2026-06-17T10:00:00Z"
  }
};

export const glossaryMatch: GlossaryTermMatch = {
  start: 9,
  end: 13,
  matched_text: "file",
  term: {
    id: "term-1",
    project_id: "project-1",
    source_language: "en",
    target_language: "pl",
    source_term: "file",
    target_term: "plik",
    definition: "A document stored by the application.",
    domain: "software",
    case_sensitive: false,
    forbidden: false,
    example_source: "Save the file.",
    example_target: "Zapisz plik."
  }
};

export const spellcheckIssue: SpellcheckIssue = {
  start: 7,
  end: 10,
  token: "plk",
  message: "Unknown word 'plk' for language 'pl'.",
  suggestions: [{ value: "plik" }],
  rule_code: "LOCAL_DICTIONARY_UNKNOWN_WORD",
  language: "pl"
};
