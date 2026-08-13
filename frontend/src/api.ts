import type { Document, QueryRun, RuntimeHealth, Workspace } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(payload.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<RuntimeHealth>("/api/health"),
  workspaces: () => request<Workspace[]>("/api/workspaces"),
  createWorkspace: (name: string) =>
    request<Workspace>("/api/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  documents: (workspaceId: string) =>
    request<Document[]>(`/api/workspaces/${workspaceId}/documents`),
  upload: (workspaceId: string, file: File, ocr: boolean) => {
    const data = new FormData();
    data.set("file", file);
    data.set("ocr", String(ocr));
    return request<Document>(`/api/workspaces/${workspaceId}/documents`, {
      method: "POST",
      body: data,
    });
  },
  query: (workspaceId: string, question: string) =>
    request<QueryRun>(`/api/workspaces/${workspaceId}/queries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  run: (runId: string) => request<QueryRun>(`/api/runs/${runId}`),
  cancel: (runId: string) => request<QueryRun>(`/api/runs/${runId}/cancel`, { method: "POST" }),
};

