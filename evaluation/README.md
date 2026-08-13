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
- a bilingual primary review, plus independent adjudication for every partial, insufficient,
  contradictory, and prompt-injection case and for any other disputed or uncertain case;
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

The expected pre-review verdict is `Corpus complete but human approval pending`. Reviewers must inspect
the rendered files, then complete copies of `reviews.template.jsonl` and
`adjudications.template.jsonl`. Template placeholders are intentionally invalid and cannot be applied.

Apply accountable review records and regenerate the runtime boundary:

```powershell
.venv\Scripts\python.exe validate.py corpus-apply-reviews `
  --reviews PATH_TO_COMPLETED_REVIEWS.jsonl `
  --adjudications PATH_TO_COMPLETED_ADJUDICATIONS.jsonl
.venv\Scripts\python.exe validate.py corpus-compile
```

Lock only after all 60 cases are approved and all mandatory adjudications are complete:

```powershell
.venv\Scripts\python.exe validate.py corpus-lock `
  --output evaluation\corpora\crag-gold-v1
.venv\Scripts\python.exe validate.py corpus-verify-lock `
  --corpus evaluation\corpora\crag-gold-v1
```

Locking never overwrites an existing directory. Any legitimate post-lock change requires a new version;
previous locked versions stay intact. Do not run the final benchmark against the draft corpus.

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
