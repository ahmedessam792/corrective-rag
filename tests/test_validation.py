import json

import pytest
from crag.domain import EvaluationLabel
from crag.evaluation import BenchmarkCase, audit_manifest, correction_metrics, load_manifest
from crag.runtime import Evaluation, OllamaRuntime


def test_manifest_audit_blocks_pending_and_missing_fixtures(tmp_path) -> None:
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "en-answerable-01",
                "language": "en",
                "category": "answerable",
                "question": "What is supported?",
                "fixture": "missing.pdf",
                "label_status": "pending_human_anchor",
            }
        ),
        encoding="utf-8",
    )
    audit = audit_manifest(load_manifest(manifest), tmp_path)
    assert not audit.acceptance_ready
    assert audit.approved_cases == 0
    assert audit.missing_fixtures == ("missing.pdf",)


def test_approved_manifest_requires_resolvable_human_anchors(tmp_path) -> None:
    (tmp_path / "source.docx").write_bytes(b"fixture")
    case = BenchmarkCase(
        id="en-answerable-01",
        language="en",
        category="answerable",
        question="What is supported?",
        fixture="source.docx",
        label_status="approved",
        reviewer="reviewer-1",
        expected_disposition="answered",
        gold_evidence=[{"text_contains": "Supported passage."}],
    )
    assert audit_manifest([case], tmp_path).acceptance_ready


def test_correction_metrics_report_improvement_and_regression() -> None:
    metrics = correction_metrics(
        pre_rankings=[["x", "gold"], ["gold", "x"], ["x", "gold"]],
        post_rankings=[["gold", "x"], ["x", "gold"], ["x", "gold"]],
        relevant=[{"gold"}, {"gold"}, {"gold"}],
        k=2,
    )
    assert metrics.improved == 1
    assert metrics.regressed == 1
    assert metrics.unchanged == 1


async def test_structured_output_repair_is_bounded(monkeypatch) -> None:
    runtime = OllamaRuntime("http://127.0.0.1:11434", "chat:tag", "embed:tag", repair_attempts=1)
    attempts: list[int] = []

    async def fake_chat(operation, prompt, schema, repair_attempt):
        attempts.append(repair_attempt)
        if repair_attempt == 0:
            raise json.JSONDecodeError("invalid", "", 0)
        return Evaluation(label=EvaluationLabel.RELEVANT)

    monkeypatch.setattr(runtime, "_chat_once", fake_chat)
    result = await runtime._structured("evaluate", "prompt", Evaluation)
    assert result.label == EvaluationLabel.RELEVANT
    assert attempts == [0, 1]


async def test_structured_output_failure_stops_after_bound(monkeypatch) -> None:
    runtime = OllamaRuntime("http://127.0.0.1:11434", "chat:tag", "embed:tag", repair_attempts=1)
    attempts: list[int] = []

    async def fake_chat(operation, prompt, schema, repair_attempt):
        attempts.append(repair_attempt)
        raise json.JSONDecodeError("invalid", "", 0)

    monkeypatch.setattr(runtime, "_chat_once", fake_chat)
    with pytest.raises(RuntimeError, match="after 2 attempt"):
        await runtime._structured("evaluate", "prompt", Evaluation)
    assert attempts == [0, 1]
