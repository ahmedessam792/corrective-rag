# Validation failed / changes required

Date: 2026-08-13  
Machine: Intel i7-8850H, 32 GB RAM, NVIDIA Quadro P600 4 GB, Windows 10 19045  
Runtime: Ollama 0.32.9  
Models: `qwen3.5:4b-q4_K_M` (`2a654d98e6fb…`) and `qwen3-embedding:0.6b` (`ac6da0dfba84…`)

This is the only current verdict. It is not an acceptance result: the locked 60-case corpus has zero approved labels and all 50 fixture files are absent.

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

Raw local artifacts are under ignored `.evaluation-runs/`, including valid runs `20260813T161839Z-8fdc7746` and `20260813T162939Z-48110574`.

## Failed or blocked gates

| Gate | Exact evidence | Classification | Smallest next action |
|---|---|---|---|
| Locked normal-RAG vs CRAG comparison | 0/60 cases approved; 50/50 fixtures missing | Evaluation | A bilingual reviewer must approve exact fixtures, dispositions, claims, and evidence anchors before the one-time run. |
| Verifier safety | No blinded human claim labels exist, so false-SUPPORTED rate cannot be established | Evaluation | Complete claim-level bilingual review and second-adjudicator review for disputed safety cases. |
| Correction effectiveness | Provisional EN improved; provisional AR did not trigger and failed Recall@6 | Model/retrieval | On a new calibration case, inspect Arabic grader semantics and one Arabic rewrite prompt; do not alter release safety rules. |
| Target-machine GPU viability | 4B GPU warm-up crashed with `0xc0000005` | Runtime/hardware | Test a pinned newer Ollama build or llama.cpp with the same GGUF; retain CPU-only as the stable control. |
| Target-machine latency | One correction path took 163.5 seconds; too little locked data exists for p95 | Runtime/hardware | After runtime stability, run the full untouched calibration set; test 2B only if p95 exceeds 180 seconds. |
| Bilingual quality | Arabic correction failed provisionally; no approved 30-case Arabic results exist | Model/retrieval/evaluation | Obtain approved Arabic anchors and evaluate Arabic independently. |
| OCR | Docling 2.119.0 is installed, but page-accurate EN/AR scan citations have not been exercised | OCR/evaluation | Run one reviewed EN scan and one reviewed AR scan; correct page anchoring if either citation is ambiguous. |
| Full application smoke | Direct real workflow is proven, but real SSE replay and active Ollama cancellation have not been recorded end-to-end through the browser/API | Runtime/application | Run the operational smoke checklist and attach the API/SSE trace before acceptance. |

No deterministic test result, calibration output, or successful local generation should be interpreted as a validated CRAG MVP.
