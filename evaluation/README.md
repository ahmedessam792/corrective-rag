# Local CRAG evaluation protocol

The evaluation layer deliberately separates three kinds of evidence:

1. deterministic tests protect code-level invariants;
2. the 12-case provisional calibration corpus is used for plumbing, prompts, and bounded model experiments;
3. the 60-case acceptance manifest is opened only after every fixture and gold anchor has bilingual human approval.

Passing deterministic tests or the calibration corpus is not an MVP validation result.

## Manifests

`calibration_cases.jsonl` contains one English and one Arabic case for each evaluation category. Its labels are provisional. Rebuild its local DOCX fixtures with:

```powershell
.venv\Scripts\python.exe evaluation\build_calibration_fixtures.py
```

`pilot_cases.jsonl` preserves the original balanced 60-case definition. Phase 6D materializes it under
`corpora/crag-gold-v1-draft/` as 60 draft cases and 60 physical sources (50 primary fixtures plus ten
independent contradiction companions). The draft is structurally complete, but no proposed label or
anchor is approved truth until the accountable human records are applied.

Each approved versioned case includes:

- one outcome: `SUPPORTED`, `PARTIAL`, `INSUFFICIENT`, or `CONTRADICTORY`;
- stable source IDs and exact normalized evidence passages with source location and passage SHA-256;
- atomic claims, including absent portions for partial cases and conflicted claims for contradictions;
- an explicit correction-required decision with bridge and target anchors where applicable;
- a bilingual primary human review for all 60 cases, plus an independent machine-assisted safety/dispute
  audit for every partial, insufficient, contradictory, and prompt-injection case;
- source provenance, binary SHA-256, and every physical fixture.

## Phase 6D corpus workflow

Rebuild the draft from the frozen 60-case definition:

```powershell
.venv\Scripts\python.exe evaluation\build_gold_corpus.py
```

The generated `runtime_cases.jsonl` contains only opaque case IDs, questions, and source references.
Expected outcomes, claims, anchors, correction labels, reviews, and notes remain in evaluator-only files.

Audit the draft:

```powershell
.venv\Scripts\python.exe validate.py corpus-audit
```

Before review, the expected verdict is `Corpus complete but human approval pending`. The current reviewed
draft reports `Corpus review complete and lock-eligible`. Reviewers must inspect the rendered files. Prepare
six ten-case bilingual primary packets, grouped by category, with:

```powershell
.venv\Scripts\python.exe validate.py corpus-prepare-review-batches --stage primary
```

The generated `review-batches/primary/` directory contains Markdown evidence packets, machine-readable
packet JSON, and one response template per batch. The packet index binds the material to the current gold
and source manifests by SHA-256. Template placeholders are intentionally invalid and cannot be applied.
All packet content is evaluator-only and must never be passed to the runtime.
The current draft already includes these generated packets. Copy response templates to reviewer-owned
working files before editing them. Regeneration is idempotent for unchanged artifacts and refuses to
overwrite any changed packet or response file; use a new `--output` directory when preserving review work.

After all 60 primary records have been completed and applied, the repository can prepare independent
adjudication packets with:

```powershell
.venv\Scripts\python.exe validate.py corpus-apply-reviews `
  --reviews PATH_TO_ALL_60_COMPLETED_PRIMARY_REVIEWS.jsonl
.venv\Scripts\python.exe validate.py corpus-prepare-review-batches --stage adjudication
```

That command refuses to run before every required primary record exists. It includes the preserved
primary decision and creates packets for all mandatory or uncertainty-triggered adjudications. For this
corpus version, the packets were used as evidence organization for an independent machine-assisted audit;
their response templates were not completed or applied.

The final Phase 6D protocol is **60/60 Primary Human Review + 40/40 Independent Machine-Assisted
Safety/Dispute Audit**. **No independent second-human adjudication was performed.** Machine findings are
preserved in the narrative reports under `evaluation/pre-review/` and in the structured, checksum-bound
`machine_audit.json`; they are not human review records and `adjudications.jsonl` remains empty.

If a future corpus version uses second-human adjudication, apply the same preserved 60 primary records
together with those human adjudication records, then regenerate the runtime boundary:

```powershell
.venv\Scripts\python.exe validate.py corpus-apply-reviews `
  --reviews PATH_TO_COMPLETED_REVIEWS.jsonl `
  --adjudications PATH_TO_COMPLETED_ADJUDICATIONS.jsonl
.venv\Scripts\python.exe validate.py corpus-compile
```

The 2026-08-20 final audit found all 40 safety/dispute cases semantically valid with zero corpus defects,
false `SUPPORTED` labels, integrity errors, or leakage. The draft explicitly selects
`primary_human_plus_machine_audit` and is lock-eligible. This protocol requires exact protected-content
hashes and zero official human adjudication records; the alternative `two_human_adjudication` protocol still
requires independent second-human confirmation. After explicit approval to create the release, run:

```powershell
.venv\Scripts\python.exe validate.py corpus-lock `
  --output evaluation\corpora\crag-gold-v1
.venv\Scripts\python.exe validate.py corpus-verify-lock `
  --corpus evaluation\corpora\crag-gold-v1
```

Do not bypass the guard or manufacture adjudication records. Locking never overwrites an existing directory.
Any legitimate post-lock change requires a new version;
previous locked versions stay intact. Review packets and unfilled templates are excluded from the locked
release; signed review and adjudication records remain. Do not run the final benchmark against the draft corpus.

Current Phase 6D release: `evaluation/corpora/crag-gold-v1`, checksum-verified and benchmark-ready. The
Phase 6E-A locked benchmark harness is implemented; no locked-corpus inference has been run.

Audit readiness:

```powershell
.venv\Scripts\python.exe validate.py audit
.venv\Scripts\python.exe validate.py audit --manifest evaluation\calibration_cases.jsonl --fixtures evaluation\calibration-fixtures
```

The command exits non-zero until the selected manifest is acceptance-ready. Provisional calibration runs must explicitly use `--allow-provisional`.

## Paired run

Configure `.env` for the exact local Ollama tags, then run:

```powershell
.venv\Scripts\python.exe validate.py run `
  --manifest evaluation\calibration_cases.jsonl `
  --fixtures evaluation\calibration-fixtures `
  --allow-provisional
```

For each case, the harness counterbalances:

- normal RAG: shared initial retrieval → shared answer model → structural citation-ID validation;
- CRAG: retrieval → grading → at most one rewrite/retrieval → evidence verification → generation/refusal → claim verification.

Both paths use the same prebuilt index, embedding model, candidate limit, context budget, answer model, seed, and generation configuration. Outputs are written under ignored `.evaluation-runs/` directories. Each run contains model/config digests, cold-start samples, stage/token telemetry, pre/post rankings, RAM/VRAM samples, predictions, mechanical metrics, and human-review templates.

Never rerun a case because its answer was unfavorable. Repeat only a documented infrastructure-corrupted run. Do not tune after viewing the locked 60-case results.

## Locked Phase 6E benchmark harness

Validate the locked corpus and frozen counterbalanced schedule without contacting the model runtime:

```powershell
.venv\Scripts\python.exe validate.py locked-benchmark-validate `
  --corpus evaluation\corpora\crag-gold-v1 `
  --expected-corpus-sha256 2b3d18599f225c83193d0ea4aa46742ffede5bdeccc521a858fc162c31c44054
```

After a separately approved Phase 6E-B runtime preflight, the full locked command is:

```powershell
.venv\Scripts\python.exe validate.py locked-run `
  --corpus evaluation\corpora\crag-gold-v1 `
  --expected-corpus-sha256 2b3d18599f225c83193d0ea4aa46742ffede5bdeccc521a858fc162c31c44054 `
  --output .evaluation-runs\locked
```

`locked-run` has no provisional or case-subset option. It rejects deterministic/mock runtimes, requires a
checksum-valid locked and benchmark-ready corpus, uses one index per paired case, and aborts on unequal
initial rankings when both pipelines retrieved successfully. The 60-case schedule is frozen and balanced
30/30 overall and 5/5 inside every category. Correction scoring uses target anchors; bridge anchors are
retained as trace metadata but cannot create correction uplift. Execution also requires a clean committed
Git worktree and fails if that Git state changes during the run.
The locked command also refuses any departure from the documented model tags, context/output limits,
CPU-only offload setting, correction bound, context-chunk count, repair bound, keep-alive, or seed-42
schedule; experiments belong outside this first locked baseline.

A completed run is sealed with `completion-manifest.json` and `artifact-checksums.sha256`. Verify it with:

```powershell
.venv\Scripts\python.exe validate.py locked-run-verify --run-dir .evaluation-runs\locked\RUN_ID
```

The artifact contains the corpus/config/runtime snapshots, frozen schedule, workspace/index, paired raw
outputs, rankings, correction traces, verifier and citation records, stage/call/resource telemetry,
errors/retries, automatic metrics, and six bilingual pipeline-blinded review batches. Keep
`pipeline-blind-map.evaluator-only.json` away from human reviewers until judgments are complete. Review
templates contain placeholders only; the harness never creates human judgments. Reranking is reported as
`not_applicable` because this architecture has no reranker.

## Human adjudication and verdict

Complete the generated human-judgment and operational-evidence templates. Judge English and Arabic separately and inspect every emitted or rejected CRAG claim. Then issue the single final verdict:

```powershell
.venv\Scripts\python.exe validate.py report `
  --run-dir .evaluation-runs\RUN_ID `
  --judgments .evaluation-runs\RUN_ID\human-judgments.jsonl `
  --operational .evaluation-runs\RUN_ID\operational-evidence.json
```

The final report cannot be generated from model outputs alone. It requires human support/citation decisions and explicit real-runtime smoke, cancellation, restart, injection, and OCR evidence.

Hard safety rules include zero false `SUPPORTED` decisions, zero unsupported released claims, and zero fabricated citations. The full thresholds and experiment ladder are in [the validation runbook](../docs/VALIDATION.md).
