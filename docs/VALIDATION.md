# Real local CRAG validation runbook

## Required setup

Use the target laptop on AC power with a fixed Windows performance profile and no competing GPU workload. Record the initial free RAM and keep the machine configuration unchanged throughout a paired run.

Required local components:

- a pinned native Windows Ollama release with cloud features unused;
- exact `qwen3.5:4b-q4_K_M` and `qwen3-embedding:0.6b` tags;
- the locked Python and frontend dependencies;
- the `docling` optional dependency for the scanned-PDF smoke gate;
- a bilingual reviewer and a second adjudicator for disputed safety labels.

Use `num_ctx=8192`, `temperature=0`, seed `42`, `num_predict=1024`, thinking disabled, a 10-minute keep-alive, one correction maximum, and six answer-context chunks for the first measured configuration. Do not infer GPU offload from model size: record `ollama ps`, NVIDIA VRAM samples, RAM, paging/OOM behavior, and actual latency.

Raw documents, prompts, evidence, and outputs stay in ignored local artifacts. No remote judge, cloud fallback, external telemetry, or automatic content transmission is allowed.

## Gate sequence

1. Freeze a reproducible Git commit and record the dependency locks and machine snapshot.
2. Build and review the disjoint calibration corpus. Keep the 60-case acceptance set unopened.
3. Run deterministic tests and validate manifest anchors and metric calculations.
4. Run the real API path for EN/AR PDF, DOCX, and scanned PDF cases, observing every CRAG stage and citation/refusal result.
5. Cancel once during embedding and once during an active chat call; require a terminal cancellation within five seconds. Restart once with an active run; require explicit reconciliation rather than a stuck status.
6. Run the provisional calibration comparison and make only measured, bounded changes.
7. Freeze exactly one configuration, audit the 60-case manifest, and run it once with counterbalanced pipeline order.
8. Conduct blinded bilingual claim/citation review, complete operational evidence, and generate the verdict report.

## Calibration experiment ladder

Change one factor at a time and retain all failed traces.

- Retrieval failure: first try the same Qwen embedding model with a documented query instruction; then, and only then, compare `bge-m3` with a rebuilt but otherwise identical index.
- Structured-output or verifier failure: try one schema/prompt correction with one bounded repair. If safety still fails and RAM measurements permit it, test `qwen3.5:9b-q4_K_M`.
- Latency or memory failure: test `qwen3.5:2b-q4_K_M`; reject it if any safety floor regresses.
- Ollama runtime failure: test llama.cpp only when the failure is cancellation, stability, or offload behavior intrinsic to Ollama.
- Ranking failure: add a local reranker only after retrieval evidence shows ranking remains the bottleneck.

Never optimize before measuring, combine several changes in one comparison, or tune against acceptance cases.

## Acceptance thresholds

- Real workflow: every stage completes using local models; citation IDs resolve; correction stays bounded; cancellation and replay work; no content leaves the machine.
- Verifier: zero false `SUPPORTED`, zero unsupported claims released, 100% citation correctness, support F1 at least 0.85 overall and 0.80 per language.
- CRAG comparison: unsupported-claim rate improves by at least 10 percentage points, or by 50% relatively when baseline error is under 10%; mean answer utility drops by no more than 0.10 on the 0–2 human scale.
- Correction: for each language, at least three of five correction cases improve, no more than one regresses, and post-correction Recall@6 is at least 0.80.
- Language: English and Arabic independently satisfy safety gates; retrieval/answer metrics are never hidden behind an aggregate.
- Laptop: warm CRAG median at most 90 seconds, p95 at most 180 seconds, median TTFT at most 30 seconds, cold readiness at most 180 seconds, peak RAM at most 28 GB, and no OOM, swapping, or silent fallback.
- OCR: EN/AR scanned-PDF evidence must retain page-usable anchors. An OCR-only failure may yield “Validated with limitations”; it cannot be hidden.

## Verdict rules

The final report emits exactly one of:

- **Validated CRAG MVP** when every hard gate passes;
- **Validated with limitations** only when all safety, comparative, bilingual, and warm-runtime gates pass but a documented noncritical gate such as optional OCR remains limited;
- **Validation failed / changes required** for any false support, unsupported release, fabricated citation, failure to beat normal RAG, correction regression, core language failure, unusable runtime, privacy failure, or unauditable result.

Every failed gate records its exact cases/metric, why it blocks or limits validation, its failure class, and the smallest next controlled action. A new untouched acceptance set is required after tuning against an opened acceptance corpus.
