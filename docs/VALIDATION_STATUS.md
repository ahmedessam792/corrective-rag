# Validation failed / changes required

Date: 2026-08-13  
Machine: Intel i7-8850H, 32 GB RAM, NVIDIA Quadro P600 4 GB, Windows 10 19045  
Runtime: Ollama 0.32.9  
Models: `qwen3.5:4b-q4_K_M` (`2a654d98e6fb…`) and `qwen3-embedding:0.6b` (`ac6da0dfba84…`)

This is the only current MVP verdict. It is not an acceptance result. Phase 6D corpus review is complete
under the documented revised protocol: all 60 cases received primary human review and all 40
safety/dispute-sensitive cases received an independent machine-assisted audit. No locked corpus exists
and Phase 6E has not started.

## Evidence collected

- The real local model and embedding paths execute successfully in CPU-only mode with valid streamed JSON-schema responses.
- A two-case EN/AR smoke run completed without runtime failures. Normal RAG took 20.7–22.9 seconds and CRAG took 54.5–82.0 seconds. Measured cold chat loads were 6.7–7.6 seconds. Peak system RAM was approximately 25.6 GB; GPU VRAM remained at zero.
- Automatic GPU offload is not viable with the current stack. Ollama offloaded 16/34 layers, allocated approximately 1.38 GB GPU model memory plus KV/compute buffers, then the llama-server crashed during warm-up with Windows access violation `0xc0000005`.
- An infrastructure-valid isolated correction experiment showed:
  - English: gold evidence moved from rank 16 to rank 1, normal RAG refused, and CRAG answered after one rewrite. CRAG latency was 163.5 seconds.
  - Arabic: correction did not trigger, gold evidence remained outside Recall@6, and CRAG refused after 74.0 seconds.
  - Aggregate correction: improvement 1, no change 1, regression 0; Recall@6 remained 0.5 while MRR improved from 0.1625 to 0.5625.
- A preliminary full calibration attempt completed 24 paired outputs but contained three Ollama HTTP 500 failures and then failed during resource sampling. It is retained as diagnostic evidence, not a valid benchmark.
- Deterministic safety and contract tests pass: 17 backend tests, including conflicting claim rejection, fabricated citations, bounded schema repair, active-stage cancellation, restart reconciliation, prompt isolation, and manifest gating.
- Frontend type checking, one browser test, and the production build pass.

Raw local artifacts are under ignored `.evaluation-runs/`. Run `20260813T161839Z-8fdc7746` is usable only for runtime smoke/resource evidence because its two cases shared a workspace. Run `20260813T162939Z-48110574` is the infrastructure-valid, case-isolated correction experiment.

## Failed or blocked gates

| Gate | Exact evidence | Classification | Smallest next action |
|---|---|---|---|
| Locked normal-RAG vs CRAG comparison | Phase 6D review evidence is complete and the aligned gate reports the draft lock-eligible, but no locked corpus or 60-case execution exists | Evaluation | Review the pre-lock report, explicitly authorize the one-time lock, then execute Phase 6E separately. |
| Verifier safety | Gold labels are primary-human reviewed and machine-audited, but no locked model outputs exist, so runtime false-SUPPORTED rate is not yet established | Evaluation | Lock the audited corpus, then measure the Phase 6E verifier confusion matrix and false-SUPPORTED rate. |
| Correction effectiveness | Provisional EN improved; provisional AR did not trigger and failed Recall@6 | Model/retrieval | On a new calibration case, inspect Arabic grader semantics and one Arabic rewrite prompt; do not alter release safety rules. |
| Target-machine GPU viability | 4B GPU warm-up crashed with `0xc0000005` | Runtime/hardware | Test a pinned newer Ollama build or llama.cpp with the same GGUF; retain CPU-only as the stable control. |
| Target-machine latency | One correction path took 163.5 seconds; too little locked data exists for p95 | Runtime/hardware | After runtime stability, run the full untouched calibration set; test 2B only if p95 exceeds 180 seconds. |
| Bilingual quality | Arabic correction failed provisionally; no approved 30-case Arabic results exist | Model/retrieval/evaluation | Obtain approved Arabic anchors and evaluate Arabic independently. |
| OCR | Docling 2.119.0 is installed, but page-accurate EN/AR scan citations have not been exercised | OCR/evaluation | Run one reviewed EN scan and one reviewed AR scan; correct page anchoring if either citation is ambiguous. |
| Full application smoke | Direct real workflow is proven, but real SSE replay and active Ollama cancellation have not been recorded end-to-end through the browser/API | Runtime/application | Run the operational smoke checklist and attach the API/SSE trace before acceptance. |

No deterministic test result, calibration output, or successful local generation should be interpreted as a validated CRAG MVP.

## Phase 6D review handoff — 2026-08-14

- The deep corpus audit still reports 60/60 structurally complete cases, 60/60 accessible sources,
  zero integrity failures, and zero runtime/gold-data leakage errors.
- Six evaluator-only bilingual primary-review batches are prepared under
  `evaluation/corpora/crag-gold-v1-draft/review-batches/primary/`; each contains five English and five
  Arabic cases from one frozen category and is hash-bound to the current gold and source manifests.
- Human status remains 0/60 reviewed, 0/60 approved, and 0/40 independently adjudicated. The guarded
  adjudication exporter correctly refuses to run until the 40 mandatory cases have primary records.
- The full deterministic suite now passes 27 tests. No acceptance benchmark was run and no locked corpus
  version was created.

## Phase 6D final review status — 2026-08-20

- Final review protocol: **60/60 Primary Human Review + 40/40 Independent Machine-Assisted
  Safety/Dispute Audit**.
- **No independent second-human adjudication was performed.** Official adjudication records remain
  empty; machine review is documented as audit evidence, not as human adjudication.
- The final source-level audit confirmed all 40 safety/dispute-sensitive cases. Ten contradiction cases
  remain intentionally unresolved at the fact level because both anchored statements are valid and no
  version, date, authority, supersession, or precedence rule resolves them. Their `CONTRADICTORY` labels
  are therefore confirmed.
- Corpus integrity remains clean: 60 cases, 60 sources, expected bilingual/category/outcome distribution,
  six current revision-2 cases, matching source and anchor hashes, no stale or duplicate primary-review
  records, and no runtime/gold-data leakage.
- Phase 6D is complete under the revised protocol. The explicit `primary_human_plus_machine_audit` gate now
  binds the audit to the exact gold semantics, sources, runtime manifest, primary reviews, and empty official
  adjudication manifest. The independent `two_human_adjudication` path remains strict.
- The draft is lock-eligible, but the official lock still requires separate user authorization.
- No corpus lock or Phase 6E benchmark was run.
