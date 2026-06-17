export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
};

export type Project = {
  id: string;
  name: string;
  source_language: string;
  target_language: string;
  domain?: string | null;
  created_at: string;
};

export type Document = {
  id: string;
  project_id: string;
  filename: string;
  source_language: string;
  target_language: string;
  status: string;
  created_at: string;
};

export type Segment = {
  id: string;
  document_id: string;
  position: number;
  source_text: string;
  target_text?: string | null;
  status: string;
  locked: boolean;
  created_at: string;
  updated_at: string;
};

export type TranslationMemoryEntry = {
  id: string;
  source_language: string;
  target_language: string;
  source_text: string;
  target_text: string;
  normalized_source_text: string;
  domain?: string | null;
  project_id?: string | null;
  created_by?: string | null;
  created_at: string;
};

export type TranslationMemorySuggestion = {
  entry: TranslationMemoryEntry;
  score: number;
  match_type: "exact" | "fuzzy";
};

export type TranslationMemorySearchRequest = {
  source_language: string;
  target_language: string;
  source_text: string;
  domain?: string | null;
  project_id?: string | null;
  limit?: number;
  min_score?: number;
};

export type TranslationMemorySearchResponse = {
  suggestions: TranslationMemorySuggestion[];
};

export type GlossaryTerm = {
  id: string;
  project_id?: string | null;
  source_language: string;
  target_language: string;
  source_term: string;
  target_term: string;
  definition?: string | null;
  domain?: string | null;
  case_sensitive: boolean;
  forbidden: boolean;
  example_source?: string | null;
  example_target?: string | null;
};

export type GlossaryTermCreateRequest = {
  project_id?: string | null;
  source_language: string;
  target_language: string;
  source_term: string;
  target_term: string;
  definition?: string | null;
  domain?: string | null;
  case_sensitive?: boolean;
  forbidden?: boolean;
  example_source?: string | null;
  example_target?: string | null;
};

export type GlossaryTermUpdateRequest = Partial<GlossaryTermCreateRequest>;

export type GlossarySearchRequest = {
  source_language: string;
  target_language: string;
  source_text: string;
  domain?: string | null;
  project_id?: string | null;
};

export type GlossaryTermMatch = {
  term: GlossaryTerm;
  start: number;
  end: number;
  matched_text: string;
};

export type GlossarySearchResponse = {
  matches: GlossaryTermMatch[];
};

export type GlossaryImportResponse = {
  imported_count: number;
  terms: GlossaryTerm[];
};

export type TerminologyViolation = {
  term: GlossaryTerm;
  violation_type: "missing_required" | "forbidden_present";
  message: string;
  start: number;
  end: number;
  matched_text: string;
};

export type TerminologyValidationError = {
  violations: TerminologyViolation[];
};
