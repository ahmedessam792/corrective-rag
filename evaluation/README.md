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

`pilot_cases.jsonl` reserves the balanced 60-case acceptance set. It is currently blocked: all fixture documents and human anchors are missing. Do not change its labels to `approved` until a bilingual reviewer has checked the exact evidence and expected disposition. A disputed safety-critical label also needs an adjudicator.

Each approved case must include:

- `expected_disposition`: `answered`, `partial`, `refused`, or `conflicting`;
- exact `gold_evidence` text anchors, optional page/paragraph anchors, and graded relevance;
- atomic `gold_claims`, including unsupported portions for partial cases;
- `reviewer`, plus `adjudicator` when required;
- every required fixture in the selected fixture directory.

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
