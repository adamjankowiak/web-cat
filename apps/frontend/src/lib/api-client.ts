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

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  const payload = await response.text();

  if (!response.ok) {
    throw new Error(payload || `API request failed with status ${response.status}`);
  }

  return JSON.parse(payload) as T;
}
