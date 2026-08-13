import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import type {
  Citation,
  Document,
  ProgressEvent,
  QueryRun,
  RuntimeHealth,
  Workspace,
} from "./types";

const eventTone: Record<string, string> = {
  retrieval_started: "retrieval",
  retrieval_completed: "retrieval",
  evaluation_weak: "correction",
  query_rewritten: "correction",
  retrieval_retry_started: "correction",
  evidence_verified: "verified",
  generation_completed: "verified",
  insufficient_evidence: "unsupported",
  failed: "unsupported",
};

function Mark({ children }: { children: ReactNode }) {
  return <span className="brand-mark" aria-hidden="true">{children}</span>;
}

function locationLabel(citation: Citation) {
  if (citation.anchor.page) return `Page ${citation.anchor.page}`;
  if (citation.anchor.heading_path.length) return citation.anchor.heading_path.join(" / ");
  if (citation.anchor.paragraph_start != null) return `Paragraph ${citation.anchor.paragraph_start + 1}`;
  return "Document passage";
}

function StatusGlyph({ status }: { status: Document["status"] }) {
  const glyph = status === "ready" ? "✓" : status === "failed" ? "×" : status === "needs_ocr" ? "◌" : "·";
  return <span className={`status-glyph ${status}`} aria-label={status.replace("_", " ")}>{glyph}</span>;
}

export default function App() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [active, setActive] = useState<Workspace | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [health, setHealth] = useState<RuntimeHealth | null>(null);
  const [question, setQuestion] = useState("");
  const [run, setRun] = useState<QueryRun | null>(null);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [ocrFiles, setOcrFiles] = useState<Record<string, File>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([api.workspaces(), api.health()])
      .then(([items, runtime]) => {
        setWorkspaces(items);
        setActive(items[0] ?? null);
        setHealth(runtime);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    if (!active) return;
    api.documents(active.id).then(setDocuments).catch((reason: Error) => setError(reason.message));
    setRun(null);
    setEvents([]);
    setSelectedCitation(null);
  }, [active]);

  const terminal = run && ["completed", "refused", "failed", "cancelled"].includes(run.status);
  useEffect(() => {
    if (!run || terminal) return;
    const source = new EventSource(`/api/runs/${run.id}/events`);
    const kinds = [
      "retrieval_started", "retrieval_completed", "evaluation_started", "evaluation_completed",
      "evaluation_weak", "query_rewritten", "retrieval_retry_started", "verification_started",
      "evidence_verified", "generation_started", "citation_validation_completed",
      "claim_verification_completed", "runtime_call_completed", "generation_completed",
      "insufficient_evidence", "failed", "cancelled",
    ];
    kinds.forEach((kind) => source.addEventListener(kind, (event) => {
      const parsed = JSON.parse((event as MessageEvent).data) as ProgressEvent;
      setEvents((current) => current.some((item) => item.id === parsed.id) ? current : [...current, parsed]);
    }));
    source.addEventListener("done", () => {
      source.close();
      api.run(run.id).then(setRun).catch((reason: Error) => setError(reason.message));
    });
    source.onerror = () => {
      api.run(run.id).then((current) => {
        setRun(current);
        if (["completed", "refused", "failed", "cancelled"].includes(current.status)) source.close();
      }).catch((reason: Error) => setError(reason.message));
    };
    return () => source.close();
  }, [run?.id, terminal]);

  const citations = useMemo(
    () => new Map((run?.result?.citations ?? []).map((citation) => [citation.id, citation])),
    [run?.result?.citations],
  );

  async function createWorkspace(name: string) {
    setBusy(true);
    setError(null);
    try {
      const workspace = await api.createWorkspace(name);
      setWorkspaces((current) => [workspace, ...current]);
      setActive(workspace);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File, ocr = false) {
    if (!active) return;
    setBusy(true);
    setError(null);
    try {
      const document = await api.upload(active.id, file, ocr);
      setDocuments((current) => [document, ...current.filter((item) => item.id !== document.id)]);
      setOcrFiles((current) => {
        const next = { ...current };
        if (document.status === "needs_ocr") next[document.id] = file;
        else delete next[document.id];
        return next;
      });
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!active || !question.trim() || busy) return;
    setBusy(true);
    setError(null);
    setEvents([]);
    setSelectedCitation(null);
    try {
      const created = await api.query(active.id, question.trim());
      setRun(created);
      setQuestion("");
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!active && workspaces.length === 0) {
    return <StartScreen busy={busy} error={error} onCreate={createWorkspace} />;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#main"><Mark>CR</Mark><span>Corrective RAG</span></a>
        <div className="workspace-switcher">
          <label htmlFor="workspace">Workspace</label>
          <select id="workspace" value={active?.id} onChange={(event) => setActive(workspaces.find((item) => item.id === event.target.value) ?? null)}>
            {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
          <button className="icon-button" onClick={() => {
            const name = window.prompt("Name this research workspace");
            if (name?.trim()) void createWorkspace(name.trim());
          }} aria-label="Create workspace">＋</button>
        </div>
        <div className={`runtime-state ${health?.ready ? "ready" : "not-ready"}`}>
          <span className="runtime-dot" />
          <span>{health?.mode ?? "checking"}</span>
          <span className="runtime-detail">{health?.detail}</span>
        </div>
      </header>

      {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError(null)}>Dismiss</button></div>}

      <main id="main" className={`workspace ${selectedCitation ? "with-evidence" : ""}`}>
        <aside className="sources-panel" aria-label="Sources">
          <div className="section-heading"><div><span className="eyebrow">Library</span><h2>Sources</h2></div><span className="count">{documents.length}</span></div>
          <button className="upload-zone" onClick={() => fileInput.current?.click()} disabled={busy}>
            <span className="upload-icon">↥</span>
            <strong>{busy ? "Processing…" : "Add evidence"}</strong>
            <small>PDF or DOCX · local only</small>
          </button>
          <input ref={fileInput} className="visually-hidden" type="file" accept=".pdf,.docx" onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void upload(file);
          }} />
          <div className="source-list">
            {documents.length === 0 && <p className="empty-copy">Your source library is empty. Add a document to begin an evidence-grounded inquiry.</p>}
            {documents.map((document) => (
              <article className="source-item" key={document.id}>
                <div className="file-monogram">{document.filename.split(".").pop()?.toUpperCase()}</div>
                <div className="source-copy">
                  <strong title={document.filename}>{document.filename}</strong>
                  <span><StatusGlyph status={document.status} /> {document.status.replace("_", " ")}</span>
                  {document.status === "needs_ocr" && ocrFiles[document.id] && (
                    <button onClick={() => void upload(ocrFiles[document.id], true)}>Retry with OCR</button>
                  )}
                  {document.error && <small title={document.error}>{document.error}</small>}
                </div>
              </article>
            ))}
          </div>
          <div className="privacy-note"><span>⌁</span><p><strong>Private by design</strong><br />Sources remain on this machine.</p></div>
        </aside>

        <section className="research-canvas" aria-label="Research canvas">
          {!run ? (
            <div className="canvas-empty">
              <span className="eyebrow">Evidence inquiry</span>
              <h1>What do you need to establish?</h1>
              <p>Ask across your sources. Weak retrieval is corrected once; unsupported claims are withheld.</p>
            </div>
          ) : (
            <div className="answer-flow">
              <div className="question-block"><span className="eyebrow">Question</span><h1>{run.question}</h1></div>
              <CorrectionTrace events={events} run={run} />
              {run.result && <Answer run={run} citations={citations} onCitation={setSelectedCitation} />}
              {run.status === "failed" && <div className="refusal"><span>Request failed</span><h2>The local workflow stopped.</h2><p>{run.error}</p></div>}
            </div>
          )}

          <form className="composer" onSubmit={ask}>
            <label className="visually-hidden" htmlFor="question">Ask a question about your sources</label>
            <textarea id="question" rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question grounded in these sources…" disabled={!documents.some((item) => item.status === "ready")} onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); }
            }} />
            <div className="composer-footer">
              <span>{documents.filter((item) => item.status === "ready").length} indexed sources</span>
              {run && !terminal ? <button type="button" className="cancel-button" onClick={() => void api.cancel(run.id).then(setRun)}>Cancel</button> : <button type="submit" className="ask-button" disabled={busy || !question.trim()}>Investigate <span>↗</span></button>}
            </div>
          </form>
        </section>

        {selectedCitation && <EvidenceLens citation={selectedCitation} onClose={() => setSelectedCitation(null)} />}
      </main>
    </div>
  );
}

function StartScreen({ busy, error, onCreate }: { busy: boolean; error: string | null; onCreate: (name: string) => Promise<void> }) {
  const [name, setName] = useState("");
  return <main className="start-screen">
    <div className="start-brand"><Mark>CR</Mark><span>Corrective RAG</span></div>
    <div className="start-content"><span className="eyebrow">Local evidence research</span><h1>Begin with a question worth proving.</h1><p>Build a private workspace where every answer can be traced back to the passage that supports it.</p>
      <form onSubmit={(event) => { event.preventDefault(); if (name.trim()) void onCreate(name.trim()); }}>
        <input aria-label="Workspace name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Name your investigation" autoFocus />
        <button disabled={busy || !name.trim()}>{busy ? "Creating…" : "Create workspace"}</button>
      </form>{error && <p role="alert" className="start-error">{error}</p>}
    </div>
    <p className="start-footnote">No cloud fallback · No document telemetry · One local researcher</p>
  </main>;
}

function CorrectionTrace({ events, run }: { events: ProgressEvent[]; run: QueryRun }) {
  const visible = events.filter((event) => !["evaluation_started", "verification_started", "generation_started"].includes(event.kind));
  return <details className="trace" open={!run.result}>
    <summary><span className="trace-pulse" /> <span>{run.result ? `Verified with ${run.correction_count + 1} retrieval pass${run.correction_count ? "es" : ""}` : "Evidence workflow in progress"}</span><span className="chevron">⌄</span></summary>
    <ol>{visible.map((event) => <li key={event.id} className={eventTone[event.kind] ?? "neutral"}><span className="trace-node" /><div><strong>{event.message}</strong><small>{event.kind.replaceAll("_", " ")}</small></div></li>)}</ol>
  </details>;
}

function Answer({ run, citations, onCitation }: { run: QueryRun; citations: Map<string, Citation>; onCitation: (citation: Citation) => void }) {
  const result = run.result!;
  if (result.disposition === "refused") return <div className="refusal"><span>Insufficient evidence</span><h2>{result.summary}</h2><p>{result.refusal_reason}</p><small>The nearest passages were not strong enough to release an answer.</small></div>;
  return <article className={`answer ${result.disposition}`}>
    <div className="answer-kicker"><span>{result.disposition === "answered" ? "Verified answer" : result.disposition === "partial" ? "Bounded partial answer" : "Evidence conflict"}</span><span>{result.claims.length} supported claim{result.claims.length === 1 ? "" : "s"}</span></div>
    <div className="claims">{result.claims.map((claim, index) => <p key={`${claim.text}-${index}`}>{claim.text} <span className="citation-cluster">{claim.citation_ids.map((id) => {
      const citation = citations.get(id);
      return <button key={id} className="citation-button" disabled={!citation} onClick={() => citation && onCitation(citation)} aria-label={`Open evidence ${id}`}>{id}</button>;
    })}</span></p>)}</div>
    {result.disposition === "partial" && <div className="partial-note"><strong>Scope note</strong><span>Only claims that passed support checks are shown; unsupported portions were withheld.</span></div>}
    {result.contradictions.map((conflict, index) => <div className="conflict-note" key={index}><strong>Conflict detected</strong><span>{conflict.summary}</span></div>)}
  </article>;
}

function EvidenceLens({ citation, onClose }: { citation: Citation; onClose: () => void }) {
  return <aside className="evidence-lens" aria-label="Evidence lens">
    <div className="lens-header"><div><span className="eyebrow">Evidence {citation.id}</span><h2>Source passage</h2></div><button className="icon-button" onClick={onClose} aria-label="Close evidence">×</button></div>
    <div className="source-meta"><div className="file-monogram">{citation.filename.split(".").pop()?.toUpperCase()}</div><div><strong>{citation.filename}</strong><span>{locationLabel(citation)}</span></div></div>
    <blockquote><span className="quote-mark">“</span>{citation.passage}</blockquote>
    <div className="anchor-details"><span>Stable source anchor</span><code>{citation.chunk_id.slice(0, 8)}</code></div>
    <p className="lens-note">This passage was selected from application-indexed evidence. Its identifier was validated before the claim was released.</p>
  </aside>;
}
