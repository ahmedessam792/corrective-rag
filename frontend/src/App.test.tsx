import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import App from "./App";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const body = url.endsWith("/api/health")
      ? { mode: "deterministic", ready: true, detail: "Offline development runtime" }
      : [];
    return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
  }));
});

test("presents the research-first empty state", async () => {
  render(<App />);
  await waitFor(() => expect(screen.getByText("Begin with a question worth proving.")).toBeInTheDocument());
  expect(screen.getByLabelText("Workspace name")).toBeInTheDocument();
  expect(screen.getByText(/No cloud fallback/)).toBeInTheDocument();
});

