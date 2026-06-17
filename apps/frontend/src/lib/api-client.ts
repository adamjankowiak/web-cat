export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
};

export type SegmentStatus = "new" | "draft" | "translated" | "reviewed" | "approved";
export type SegmentationStrategy = "sentence" | "paragraph";

export type DocumentRead = {
  id: string;
  project_id: string;
  filename: string;
  source_language: string;
  target_language: string;
  status: string;
  created_at: string;
};

export type SegmentRead = {
  id: string;
  document_id: string;
  position: number;
  source_text: string;
  target_text: string | null;
  status: SegmentStatus;
  locked: boolean;
  created_at: string;
  updated_at: string;
};

export type DocumentDetailRead = {
  document: DocumentRead;
  segments: SegmentRead[];
};

export type DocumentImportRequest = {
  filename: string;
  content: string;
  source_language: string;
  target_language: string;
  project_name?: string;
  segmentation_strategy: SegmentationStrategy;
};

export type SegmentUpdateRequest = {
  target_text?: string;
  status?: SegmentStatus;
};

export type TranslationMemoryEntryRead = {
  id: string;
  source_language: string;
  target_language: string;
  source_text: string;
  target_text: string;
  normalized_source_text: string;
  domain: string | null;
  project_id: string | null;
  created_by: string | null;
  created_at: string;
};

export type TranslationMemoryMatchType = "exact" | "fuzzy";

export type TranslationMemorySuggestion = {
  entry: TranslationMemoryEntryRead;
  score: number;
  match_type: TranslationMemoryMatchType;
};

export type TranslationMemorySearchResponse = {
  suggestions: TranslationMemorySuggestion[];
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

export type GlossaryTermRead = {
  id: string;
  project_id: string | null;
  source_language: string;
  target_language: string;
  source_term: string;
  target_term: string;
  definition: string | null;
  domain: string | null;
  case_sensitive: boolean;
  forbidden: boolean;
  example_source: string | null;
  example_target: string | null;
};

export type GlossaryTermMatch = {
  term: GlossaryTermRead;
  start: number;
  end: number;
  matched_text: string;
};

export type GlossarySearchRequest = {
  source_language: string;
  target_language: string;
  source_text: string;
  domain?: string | null;
  project_id?: string | null;
};

export type GlossarySearchResponse = {
  matches: GlossaryTermMatch[];
};

export type TerminologyViolation = {
  term: GlossaryTermRead;
  violation_type: "missing_required" | "forbidden_present" | string;
  message: string;
  start: number;
  end: number;
  matched_text: string;
};

export type TerminologyValidationDetail = {
  violations: TerminologyViolation[];
};

export type SpellcheckSuggestion = {
  value: string;
};

export type SpellcheckIssue = {
  start: number;
  end: number;
  token: string;
  message: string;
  suggestions: SpellcheckSuggestion[];
  rule_code: string;
  language: string;
};

export type SpellcheckRequest = {
  language: string;
  text: string;
  project_id?: string | null;
  created_by?: string | null;
};

export type SpellcheckResponse = {
  issues: SpellcheckIssue[];
};

export type SpellcheckIgnoreCreateRequest = {
  project_id: string;
  language: string;
  word: string;
  created_by?: string | null;
};

export type SpellcheckIgnoreRead = {
  id: string;
  project_id: string;
  language: string;
  word: string;
  created_by: string | null;
  created_at: string;
};

export class ApiError extends Error {
  detail: unknown;
  status: number;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export async function listDocuments(): Promise<DocumentRead[]> {
  return requestJson<DocumentRead[]>("/documents");
}

export async function getDocument(documentId: string): Promise<DocumentDetailRead> {
  return requestJson<DocumentDetailRead>(`/documents/${documentId}`);
}

export async function importTxtDocument(
  payload: DocumentImportRequest
): Promise<DocumentDetailRead> {
  return requestJson<DocumentDetailRead>("/documents", {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
}

export async function updateSegment(
  segmentId: string,
  payload: SegmentUpdateRequest
): Promise<SegmentRead> {
  return requestJson<SegmentRead>(`/segments/${segmentId}`, {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
}

export async function approveSegment(segmentId: string): Promise<SegmentRead> {
  return requestJson<SegmentRead>(`/segments/${segmentId}/approve`, {
    method: "POST"
  });
}

export async function searchTranslationMemory(
  payload: TranslationMemorySearchRequest
): Promise<TranslationMemorySearchResponse> {
  return requestJson<TranslationMemorySearchResponse>("/translation-memory/search", {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
}

export async function searchGlossary(
  payload: GlossarySearchRequest
): Promise<GlossarySearchResponse> {
  return requestJson<GlossarySearchResponse>("/glossary/search", {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
}

export async function checkSpelling(
  payload: SpellcheckRequest
): Promise<SpellcheckResponse> {
  return requestJson<SpellcheckResponse>("/spellcheck", {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
}

export async function ignoreSpellcheckWord(
  payload: SpellcheckIgnoreCreateRequest
): Promise<SpellcheckIgnoreRead> {
  return requestJson<SpellcheckIgnoreRead>("/spellcheck/ignore", {
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });
}

export async function listSpellcheckIgnoredWords(
  projectId: string,
  language?: string
): Promise<SpellcheckIgnoreRead[]> {
  const params = new URLSearchParams({ project_id: projectId });

  if (language) {
    params.set("language", language);
  }

  return requestJson<SpellcheckIgnoreRead[]>(`/spellcheck/ignore?${params.toString()}`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  const responseText = await response.text();
  const payload = parseResponsePayload(responseText);

  if (!response.ok) {
    throw new ApiError(
      formatApiErrorMessage(payload, response.status),
      response.status,
      payload
    );
  }

  return payload as T;
}

function parseResponsePayload(responseText: string): unknown {
  if (!responseText) {
    return null;
  }

  try {
    return JSON.parse(responseText);
  } catch {
    return responseText;
  }
}

function formatApiErrorMessage(payload: unknown, status: number): string {
  if (typeof payload === "string" && payload) {
    return payload;
  }

  if (isObjectWithDetail(payload)) {
    if (typeof payload.detail === "string") {
      return payload.detail;
    }

    if (isTerminologyValidationDetail(payload.detail)) {
      return formatTerminologyViolations(payload.detail.violations);
    }
  }

  return `API request failed with status ${status}`;
}

export function isTerminologyValidationDetail(
  detail: unknown
): detail is TerminologyValidationDetail {
  return (
    isObjectWithDetail(detail) &&
    Array.isArray(detail.violations) &&
    detail.violations.every((violation) => isObjectWithDetail(violation))
  );
}

export function formatTerminologyViolations(violations: TerminologyViolation[]): string {
  return violations
    .map((violation) => {
      if (violation.violation_type === "missing_required") {
        return `Required term missing: ${violation.term.source_term} -> ${violation.term.target_term}`;
      }

      if (violation.violation_type === "forbidden_present") {
        return `Forbidden term used: ${violation.term.target_term}`;
      }

      return violation.message;
    })
    .join(" ");
}

function isObjectWithDetail(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
