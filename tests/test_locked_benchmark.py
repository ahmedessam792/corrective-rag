import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from crag.config import Settings
from crag.locked_benchmark import (
    LockedRuntimeCase,
    _correction_metrics,
    assert_locked_baseline_configuration,
    assert_locked_runtime_settings,
    assert_paired_initial_retrieval,
    assert_real_locked_runtime,
    attribute_crag_telemetry,
    attribute_normal_telemetry,
    build_counterbalanced_schedule,
    correction_target_anchor_ids,
    generate_blinded_review_packets,
    load_locked_benchmark_corpus,
    locked_automatic_metrics,
    map_anchor_chunks,
    seal_run_artifacts,
    verify_run_artifacts,
)
from crag.validation import CaseRunRecord, run_locked_benchmark
from pydantic import ValidationError

CORPUS = Path("evaluation/corpora/crag-gold-v1")
CORPUS_SHA256 = "2b3d18599f225c83193d0ea4aa46742ffede5bdeccc521a858fc162c31c44054"


@pytest.fixture(scope="module")
def locked_bundle():
    return load_locked_benchmark_corpus(
        CORPUS,
        expected_aggregate_sha256=CORPUS_SHA256,
        verify_documents=False,
    )


def _record(case_id: str, pipeline: str, **values) -> CaseRunRecord:
    defaults = {
        "case_id": case_id,
        "language": case_id[:2],
        "category": "answerable",
        "pipeline": pipeline,
        "order": 1,
        "wall_seconds": 1.0,
        "status": "completed",
    }
    defaults.update(values)
    return CaseRunRecord.model_validate(defaults)


def test_locked_corpus_loading_keeps_runtime_inputs_gold_free(locked_bundle) -> None:
    assert locked_bundle.version == "crag-gold-v1"
    assert len(locked_bundle.runtime_cases) == 60
    assert len(locked_bundle.gold_by_id) == 60
    runtime_payload = locked_bundle.runtime_cases[0].model_dump()
    assert set(runtime_payload) == {"id", "question", "sources"}
    assert not ({"expected_outcome", "gold_evidence", "correction"} & set(runtime_payload))


def test_locked_runtime_schema_refuses_gold_leakage(locked_bundle) -> None:
    payload = locked_bundle.runtime_cases[0].model_dump(mode="json")
    payload["expected_outcome"] = "SUPPORTED"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        LockedRuntimeCase.model_validate(payload)


def test_locked_corpus_refuses_checksum_mismatch(tmp_path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    runtime_manifest = copied / "runtime_cases.jsonl"
    runtime_manifest.write_text(runtime_manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="checksum verification failed"):
        load_locked_benchmark_corpus(copied, expected_aggregate_sha256=CORPUS_SHA256)


def test_locked_execution_refuses_deterministic_and_mock_runtimes() -> None:
    with pytest.raises(RuntimeError, match="runtime=ollama"):
        assert_real_locked_runtime(Settings(runtime="deterministic"), object(), object())
    with pytest.raises(RuntimeError, match="concrete Ollama"):
        assert_real_locked_runtime(Settings(runtime="ollama"), object(), object())
    with pytest.raises(RuntimeError, match="loopback-only"):
        assert_locked_runtime_settings(
            Settings(runtime="ollama", ollama_url="https://runtime.example.invalid")
        )
    with pytest.raises(RuntimeError, match="frozen Phase 6E"):
        assert_locked_baseline_configuration(Settings(runtime="ollama"), schedule_seed=7)


async def test_locked_runner_refuses_deterministic_before_creating_artifacts(tmp_path) -> None:
    output = tmp_path / "runs"
    with pytest.raises(RuntimeError, match="runtime=ollama"):
        await run_locked_benchmark(
            CORPUS,
            output,
            Settings(runtime="deterministic"),
            expected_corpus_sha256=CORPUS_SHA256,
        )
    assert not output.exists()


def test_counterbalanced_schedule_is_frozen_and_stratified(locked_bundle) -> None:
    first = build_counterbalanced_schedule(locked_bundle, seed=42)
    second = build_counterbalanced_schedule(locked_bundle, seed=42)
    assert first == second
    assert sum(entry.pipeline_order[0] == "normal_rag" for entry in first) == 30
    for offset in range(0, 60, 12):
        assert len({entry.category for entry in first[offset : offset + 12]}) == 6
    for category in {entry.category for entry in first}:
        category_entries = [entry for entry in first if entry.category == category]
        assert len(category_entries) == 10
        assert sum(entry.pipeline_order[0] == "normal_rag" for entry in category_entries) == 5
        for number in range(1, 6):
            pair = [entry for entry in category_entries if entry.case_id.endswith(f"-{number:02d}")]
            assert {entry.language for entry in pair} == {"en", "ar"}
            assert {entry.pipeline_order[0] for entry in pair} == {"normal_rag", "crag"}


def test_paired_initial_retrieval_fairness_detects_difference() -> None:
    matching = [
        _record("en-answerable-01", "normal_rag", initial_ranking=["a", "b"]),
        _record("en-answerable-01", "crag", initial_ranking=["a", "b"]),
    ]
    assert_paired_initial_retrieval(matching)
    matching[1].initial_ranking = ["b", "a"]
    with pytest.raises(RuntimeError, match="initial rankings differ"):
        assert_paired_initial_retrieval(matching)


def test_correction_scoring_uses_target_not_bridge(locked_bundle) -> None:
    case = locked_bundle.gold_by_id["en-correction-01"]
    assert correction_target_anchor_ids(case) == {"en-correction-01-ev-target"}
    record = _record(
        case.id,
        "crag",
        category="correction_required",
        correction_triggered=True,
        target_anchor_ids=["en-correction-01-ev-target"],
        scoring_chunk_ids=["target-chunk"],
        initial_ranking=["bridge-chunk", "x", "target-chunk"],
        final_ranking=["target-chunk", "bridge-chunk", "x"],
    )
    metrics = _correction_metrics([record])
    assert metrics["useful"] == 1
    assert metrics["harmful"] == 0
    assert metrics["average_target_rank_delta"] == 2.0


def test_locked_adapter_preserves_anchor_identity_role_and_relevance(locked_bundle) -> None:
    case = locked_bundle.gold_by_id["en-correction-01"]
    source = locked_bundle.source_by_id[case.source_ids[0]]
    rows = [
        {
            "id": f"chunk-{index}",
            "document_id": "document-1",
            "filename": Path(source.relative_path).name,
            "text": anchor.exact_text,
            "page": anchor.locator.page,
        }
        for index, anchor in enumerate(case.gold_evidence, start=1)
    ]

    class FakeDatabase:
        @staticmethod
        def chunk_rows(workspace_id):
            assert workspace_id == "workspace-1"
            return rows

        @staticmethod
        def row_to_chunk(row):
            return SimpleNamespace(
                anchor=SimpleNamespace(
                    page=row["page"],
                    paragraph_start=None,
                    paragraph_end=None,
                )
            )

    bindings = map_anchor_chunks(
        FakeDatabase(),
        "workspace-1",
        case,
        locked_bundle.source_by_id,
        {source.source_id: "document-1"},
    )
    by_anchor = {binding.anchor_id: binding for binding in bindings}
    target = by_anchor["en-correction-01-ev-target"]
    assert target.source_id == source.source_id
    assert target.role == "necessary"
    assert target.relevance == 3
    assert target.correction_target
    assert target.chunk_ids == ["chunk-2"]


def test_false_supported_and_failure_denominators_are_preserved(locked_bundle) -> None:
    case = locked_bundle.gold_by_id["en-unanswerable-01"]
    false_supported = _record(
        case.id,
        "crag",
        category=case.category,
        verifier_label="supported",
    )
    normal_failure = _record(case.id, "normal_rag", category=case.category, status="failed", error="timeout")
    metrics = locked_automatic_metrics([normal_failure, false_supported], {case.id: case})
    assert metrics["overall"]["crag"]["verifier"]["false_supported"] == 1
    assert metrics["overall"]["crag"]["verifier"]["false_supported_rate"] == 1.0
    assert metrics["failure_denominator"] == {
        "expected_pipeline_runs": 2,
        "recorded_pipeline_runs": 2,
        "failed_pipeline_runs": 1,
        "missing_pipeline_runs": [],
        "duplicate_pipeline_runs": [],
    }


def test_telemetry_is_attributed_to_the_correct_pipeline_stages() -> None:
    normal = attribute_normal_telemetry(
        [
            {"operation": "query_embedding", "wall_seconds": 0.2},
            {
                "operation": "draft",
                "wall_seconds": 3.0,
                "ttft_seconds": 0.5,
                "eval_count": 20,
                "eval_duration_ns": 2_000_000_000,
            },
        ],
        retrieval_seconds=0.4,
        total_seconds=3.5,
    )
    assert normal.stage_latency_seconds["retrieval"] == 0.4
    assert normal.stage_latency_seconds["reranking"] is None
    assert normal.generation_tokens_per_second == 10.0
    events = [
        {"kind": "retrieval_started", "created_at": "2026-08-20T00:00:00+00:00", "data": {"pass_number": 1}},
        {"kind": "retrieval_completed", "created_at": "2026-08-20T00:00:01+00:00", "data": {"pass_number": 1}},
        {
            "kind": "runtime_call_completed",
            "created_at": "2026-08-20T00:00:02+00:00",
            "data": {"operation": "evaluate", "wall_seconds": 2.0},
        },
        {
            "kind": "runtime_call_completed",
            "created_at": "2026-08-20T00:00:03+00:00",
            "data": {"operation": "verify", "wall_seconds": 3.0},
        },
        {"kind": "evidence_verified", "created_at": "2026-08-20T00:00:04+00:00", "data": {"label": "supported"}},
        {
            "kind": "runtime_call_completed",
            "created_at": "2026-08-20T00:00:05+00:00",
            "data": {"operation": "draft", "wall_seconds": 4.0},
        },
        {
            "kind": "runtime_call_completed",
            "created_at": "2026-08-20T00:00:06+00:00",
            "data": {"operation": "verify", "wall_seconds": 5.0},
        },
    ]
    calls = [event["data"] for event in events if event["kind"] == "runtime_call_completed"]
    crag = attribute_crag_telemetry(events, calls, total_seconds=15.0)
    assert crag.stage_latency_seconds["retrieval"] == 1.0
    assert crag.stage_latency_seconds["grading"] == 2.0
    assert crag.stage_latency_seconds["verification"] == 3.0
    assert crag.stage_latency_seconds["generation"] == 4.0
    assert crag.stage_latency_seconds["claim_verification"] == 5.0


def test_completed_run_is_immutable_and_tampering_is_detected(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "raw.json").write_text(json.dumps({"answer": 42}), encoding="utf-8")
    seal_run_artifacts(run_dir, {"run_id": "run-1", "status": "completed"})
    assert verify_run_artifacts(run_dir) == []
    with pytest.raises(FileExistsError, match="immutable"):
        seal_run_artifacts(run_dir, {"run_id": "run-1", "status": "completed"})
    (run_dir / "raw.json").write_text(json.dumps({"answer": 43}), encoding="utf-8")
    assert verify_run_artifacts(run_dir)


def test_human_review_packets_are_pipeline_blinded_and_unjudged(tmp_path, locked_bundle) -> None:
    records = []
    for case in locked_bundle.gold_by_id.values():
        records.extend(
            [
                _record(case.id, "normal_rag", language=case.language, category=case.category),
                _record(case.id, "crag", language=case.language, category=case.category),
            ]
        )
    output = generate_blinded_review_packets(tmp_path / "human-review", records, locked_bundle)
    packet_text = (output / "review-01-answerable.packet.json").read_text(encoding="utf-8")
    assert "normal_rag" not in packet_text
    assert '"pipeline"' not in packet_text
    assert (tmp_path / "pipeline-blind-map.evaluator-only.json").is_file()
    template = (output / "review-01-answerable.judgments.template.jsonl").read_text(encoding="utf-8")
    assert "REQUIRED-HUMAN-ID" in template
