export type Workspace = { id: string; name: string; created_at: string };

export type DocumentStatus = "processing" | "ready" | "needs_ocr" | "failed";
export type Document = {
  id: string;
  workspace_id: string;
  filename: string;
  media_type: string;
  sha256: string;
  status: DocumentStatus;
  ocr_requested: boolean;
  error?: string | null;
  created_at: string;
};

export type SourceAnchor = {
  page?: number | null;
  heading_path: string[];
  paragraph_start?: number | null;
  paragraph_end?: number | null;
  bounding_box?: number[] | null;
};

export type Citation = {
  id: string;
  document_id: string;
  filename: string;
  chunk_id: string;
  passage: string;
  anchor: SourceAnchor;
};

export type Claim = { text: string; citation_ids: string[] };
export type AnswerResult = {
  disposition: "answered" | "partial" | "refused" | "conflicting";
  summary: string;
  claims: Claim[];
  citations: Citation[];
  contradictions: { summary: string; citation_ids: string[] }[];
  refusal_reason?: string | null;
};

export type RunStatus = "queued" | "running" | "completed" | "refused" | "failed" | "cancelled";
export type QueryRun = {
  id: string;
  workspace_id: string;
  question: string;
  status: RunStatus;
  correction_count: number;
  rewritten_query?: string | null;
  result?: AnswerResult | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
};

export type ProgressEvent = {
  id: number;
  run_id: string;
  kind: string;
  message: string;
  data: Record<string, unknown>;
  created_at: string;
};

export type RuntimeHealth = { mode: string; ready: boolean; detail: string };

