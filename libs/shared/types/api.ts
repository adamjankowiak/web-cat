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
