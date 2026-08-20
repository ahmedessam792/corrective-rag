from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from crag.corpus import (
    CorpusStatus,
    GoldCase,
    SourceRecord,
    audit_corpus,
    file_sha256,
    load_corpus,
    normalize_extracted_text,
    verify_locked_corpus,
)
from crag.database import Database
from crag.evaluation import retrieval_metrics
from crag.ingestion import OllamaEmbedder
from crag.runtime import OllamaRuntime

CATEGORY_ORDER = (
    "answerable",
    "correction_required",
    "unanswerable",
    "partial",
    "contradictory",
    "prompt_injection",
)
PIPELINES = ("normal_rag", "crag")
RERANKING_STATUS = "not_applicable"
LOCKED_SCHEDULE_SEED = 42
LOCKED_BASELINE_SETTINGS = {
    "chat_model": "qwen3.5:4b-q4_K_M",
    "embed_model": "qwen3-embedding:0.6b",
    "ollama_context_size": 8192,
    "ollama_output_tokens": 1024,
    "ollama_seed": 42,
    "ollama_gpu_layers": 0,
    "ollama_keep_alive": "10m",
    "ollama_timeout_seconds": 180.0,
    "structured_repair_attempts": 1,
    "max_corrections": 1,
    "context_chunks": 6,
}


class LockedRuntimeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class LockedRuntimeCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    question: str = Field(min_length=2)
    sources: list[LockedRuntimeSource] = Field(min_length=1)


class ScheduleEntry(BaseModel):
    case_id: str
    pair_id: str
    language: Literal["en", "ar"]
    category: str
    pipeline_order: tuple[Literal["normal_rag", "crag"], Literal["normal_rag", "crag"]]


class AnchorChunkBinding(BaseModel):
    anchor_id: str
    source_id: str
    role: str
    relevance: int
    chunk_ids: list[str]
    correction_target: bool = False


class TelemetrySummary(BaseModel):
    stage_latency_seconds: dict[str, float | None]
    generation_ttft_seconds: float | None = None
    generation_tokens_per_second: float | None = None
    model_call_count: int = 0
    embedding_call_count: int = 0
    rewrite_call_count: int = 0
    structured_retry_count: int = 0


@dataclass(frozen=True, slots=True)
class LockedCorpusBundle:
    root: Path
    corpus_id: str
    version: str
    aggregate_sha256: str
    runtime_cases: tuple[LockedRuntimeCase, ...]
    gold_by_id: dict[str, GoldCase]
    source_by_id: dict[str, SourceRecord]
    audit: dict[str, Any]


def assert_locked_runtime_settings(settings: Any) -> None:
    if getattr(settings, "runtime", None) != "ollama":
        raise RuntimeError("Locked benchmarks require runtime=ollama; deterministic mode is forbidden")
    hostname = urlparse(str(getattr(settings, "ollama_url", ""))).hostname
    if hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Locked benchmarks require a loopback-only Ollama endpoint")


def assert_locked_baseline_configuration(settings: Any, schedule_seed: int) -> None:
    assert_locked_runtime_settings(settings)
    errors = []
    if schedule_seed != LOCKED_SCHEDULE_SEED:
        errors.append(f"schedule_seed={schedule_seed!r} (expected {LOCKED_SCHEDULE_SEED!r})")
    errors.extend(
        f"{name}={getattr(settings, name, None)!r} (expected {expected!r})"
        for name, expected in LOCKED_BASELINE_SETTINGS.items()
        if getattr(settings, name, None) != expected
    )
    if errors:
        raise RuntimeError(
            "Locked baseline configuration differs from the frozen Phase 6E values: "
            + "; ".join(errors)
        )


def assert_real_locked_runtime(settings: Any, runtime: Any, embedder: Any) -> None:
    """Reject test/provisional runtimes before a locked benchmark can start."""
    assert_locked_runtime_settings(settings)
    if type(runtime) is not OllamaRuntime or type(embedder) is not OllamaEmbedder:
        raise RuntimeError("Locked benchmarks require the concrete Ollama runtime and embedder")


def _read_runtime_cases(path: Path) -> list[LockedRuntimeCase]:
    values: list[LockedRuntimeCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            values.append(LockedRuntimeCase.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"Invalid locked runtime case at {path}:{line_number}: {exc}") from exc
    ids = [value.id for value in values]
    if len(ids) != len(set(ids)):
        raise ValueError("Locked runtime case IDs are not unique")
    return values


def load_locked_benchmark_corpus(
    root: Path,
    *,
    expected_aggregate_sha256: str | None = None,
    verify_documents: bool = True,
) -> LockedCorpusBundle:
    checksum_errors = verify_locked_corpus(root)
    if checksum_errors:
        raise RuntimeError(f"Locked corpus checksum verification failed: {checksum_errors}")
    audit = audit_corpus(root, verify_lock=True, verify_documents=verify_documents)
    if audit.status != CorpusStatus.LOCKED or not audit.benchmark_ready:
        raise RuntimeError(f"Corpus is not locked and benchmark-ready: {audit.model_dump()}")
    metadata, gold_cases, sources, _, _ = load_corpus(root)
    if not metadata.aggregate_sha256:
        raise RuntimeError("Locked corpus aggregate checksum is missing")
    if expected_aggregate_sha256 and metadata.aggregate_sha256 != expected_aggregate_sha256:
        raise RuntimeError(
            "Locked corpus aggregate checksum does not match the required benchmark version"
        )
    runtime_cases = _read_runtime_cases(root / metadata.runtime_manifest)
    gold_by_id = {case.id: case for case in gold_cases}
    source_by_id = {source.source_id: source for source in sources}
    if {case.id for case in runtime_cases} != set(gold_by_id):
        raise RuntimeError("Locked runtime and evaluator-only gold case IDs differ")
    for runtime_case in runtime_cases:
        gold = gold_by_id[runtime_case.id]
        if runtime_case.question != gold.question:
            raise RuntimeError(f"Runtime question differs from locked gold case: {gold.id}")
        expected_sources = [
            LockedRuntimeSource(
                source_id=source_id,
                relative_path=source_by_id[source_id].relative_path,
                sha256=source_by_id[source_id].sha256,
            )
            for source_id in gold.source_ids
        ]
        if runtime_case.sources != expected_sources:
            raise RuntimeError(f"Runtime source linkage differs from locked gold case: {gold.id}")
    return LockedCorpusBundle(
        root=root,
        corpus_id=metadata.corpus_id,
        version=metadata.version,
        aggregate_sha256=metadata.aggregate_sha256,
        runtime_cases=tuple(runtime_cases),
        gold_by_id=gold_by_id,
        source_by_id=source_by_id,
        audit=audit.model_dump(),
    )


def build_counterbalanced_schedule(bundle: LockedCorpusBundle, seed: int = 42) -> list[ScheduleEntry]:
    by_key: dict[tuple[str, str], dict[str, LockedRuntimeCase]] = defaultdict(dict)
    for runtime_case in bundle.runtime_cases:
        gold = bundle.gold_by_id[runtime_case.id]
        number = runtime_case.id.rsplit("-", 1)[-1]
        by_key[(gold.category, number)][gold.language] = runtime_case
    expected_keys = {(category, f"{index:02d}") for category in CATEGORY_ORDER for index in range(1, 6)}
    if set(by_key) != expected_keys or any(set(pair) != {"en", "ar"} for pair in by_key.values()):
        raise RuntimeError("Locked corpus cannot form the frozen 30 bilingual counterbalance pairs")
    rng = random.Random(seed)
    pair_keys: list[tuple[str, str]] = []
    for index in range(1, 6):
        categories = list(CATEGORY_ORDER)
        rng.shuffle(categories)
        pair_keys.extend((category, f"{index:02d}") for category in categories)
    normal_first_language = {
        key: "en" if position % 2 == 0 else "ar" for position, key in enumerate(pair_keys)
    }
    entries: list[ScheduleEntry] = []
    for position, key in enumerate(pair_keys):
        category, _ = key
        language_order = ("en", "ar") if position % 2 == 0 else ("ar", "en")
        for language in language_order:
            runtime_case = by_key[key][language]
            order = (
                ("normal_rag", "crag")
                if language == normal_first_language[key]
                else ("crag", "normal_rag")
            )
            entries.append(
                ScheduleEntry(
                    case_id=runtime_case.id,
                    pair_id=f"{bundle.version}:{runtime_case.id}",
                    language=language,
                    category=category,
                    pipeline_order=order,
                )
            )
    first_counts = Counter(entry.pipeline_order[0] for entry in entries)
    if first_counts != {"normal_rag": 30, "crag": 30}:
        raise RuntimeError(f"Counterbalanced schedule is not 30/30: {dict(first_counts)}")
    for category in CATEGORY_ORDER:
        category_counts = Counter(
            entry.pipeline_order[0] for entry in entries if entry.category == category
        )
        if category_counts != {"normal_rag": 5, "crag": 5}:
            raise RuntimeError(f"Category schedule is not balanced: {category}: {dict(category_counts)}")
    return entries


def correction_target_anchor_ids(case: GoldCase) -> set[str]:
    if case.correction.required:
        return set(case.correction.target_anchor_ids)
    return {anchor.id for anchor in case.gold_evidence if anchor.role.value != "bridge"}


def map_anchor_chunks(
    database: Database,
    workspace_id: str,
    case: GoldCase,
    source_by_id: dict[str, SourceRecord],
    document_ids_by_source: dict[str, str] | None = None,
) -> list[AnchorChunkBinding]:
    rows = database.chunk_rows(workspace_id)
    target_ids = correction_target_anchor_ids(case)
    bindings: list[AnchorChunkBinding] = []
    for anchor in case.gold_evidence:
        source = source_by_id[anchor.source_id]
        filename = Path(source.relative_path).name
        exact = normalize_extracted_text(anchor.exact_text)
        matched: list[str] = []
        for row in rows:
            if row["filename"] != filename or exact not in normalize_extracted_text(row["text"]):
                continue
            if document_ids_by_source and row["document_id"] != document_ids_by_source[anchor.source_id]:
                continue
            chunk = database.row_to_chunk(row)
            if anchor.locator.page is not None and chunk.anchor.page != anchor.locator.page:
                continue
            if anchor.locator.paragraph_start is not None:
                start = chunk.anchor.paragraph_start
                end = chunk.anchor.paragraph_end if chunk.anchor.paragraph_end is not None else start
                if start is None or end is None or not start <= anchor.locator.paragraph_start <= end:
                    continue
            matched.append(row["id"])
        bindings.append(
            AnchorChunkBinding(
                anchor_id=anchor.id,
                source_id=anchor.source_id,
                role=anchor.role,
                relevance=anchor.relevance,
                chunk_ids=sorted(matched),
                correction_target=anchor.id in target_ids,
            )
        )
    return bindings


def assert_paired_initial_retrieval(records: list[Any]) -> None:
    grouped: dict[str, dict[str, Any]] = defaultdict(dict)
    for record in records:
        grouped[record.case_id][record.pipeline] = record
    errors = []
    for case_id, values in grouped.items():
        if set(values) != set(PIPELINES):
            errors.append(f"{case_id}: missing paired pipeline")
            continue
        normal = values["normal_rag"]
        crag = values["crag"]
        if (normal.status == "failed" or crag.status == "failed") and not (
            normal.initial_ranking and crag.initial_ranking
        ):
            continue
        if normal.initial_ranking != crag.initial_ranking:
            errors.append(f"{case_id}: initial rankings differ")
    if errors:
        raise RuntimeError("Paired initial-retrieval fairness failed: " + "; ".join(errors))


def _event_seconds(start: dict[str, Any], end: dict[str, Any]) -> float:
    left = datetime.fromisoformat(start["created_at"])
    right = datetime.fromisoformat(end["created_at"])
    return max(0.0, (right - left).total_seconds())


def attribute_crag_telemetry(
    events: list[dict[str, Any]], runtime_calls: list[dict[str, Any]], total_seconds: float
) -> TelemetrySummary:
    stage: dict[str, float | None] = {
        "retrieval": 0.0,
        "reranking": None,
        "grading": 0.0,
        "rewriting": 0.0,
        "re_retrieval": 0.0,
        "verification": 0.0,
        "claim_verification": 0.0,
        "generation": 0.0,
        "total": total_seconds,
    }
    pending_retrieval: dict[int, dict[str, Any]] = {}
    evidence_verified = False
    draft_calls: list[dict[str, Any]] = []
    for event in events:
        if event["kind"] in {"retrieval_started", "retrieval_retry_started"}:
            pending_retrieval[int(event["data"].get("pass_number", 1))] = event
        elif event["kind"] == "retrieval_completed":
            pass_number = int(event["data"].get("pass_number", 1))
            started = pending_retrieval.get(pass_number)
            if started:
                key = "retrieval" if pass_number == 1 else "re_retrieval"
                stage[key] = float(stage[key] or 0.0) + _event_seconds(started, event)
        elif event["kind"] == "evidence_verified":
            evidence_verified = True
        elif event["kind"] == "runtime_call_completed":
            call = event["data"]
            operation = call.get("operation")
            seconds = float(call.get("wall_seconds") or 0.0)
            if operation == "evaluate":
                stage["grading"] = float(stage["grading"] or 0.0) + seconds
            elif operation == "rewrite":
                stage["rewriting"] = float(stage["rewriting"] or 0.0) + seconds
            elif operation == "draft":
                stage["generation"] = float(stage["generation"] or 0.0) + seconds
                draft_calls.append(call)
            elif operation == "verify":
                key = "claim_verification" if evidence_verified else "verification"
                stage[key] = float(stage[key] or 0.0) + seconds
    chat_calls = [call for call in runtime_calls if call.get("operation") in {"evaluate", "rewrite", "verify", "draft"}]
    embedding_calls = [call for call in runtime_calls if call.get("operation") == "query_embedding"]
    generated_tokens = sum(int(call.get("eval_count") or 0) for call in draft_calls)
    generated_seconds = sum(float(call.get("eval_duration_ns") or 0) for call in draft_calls) / 1_000_000_000
    return TelemetrySummary(
        stage_latency_seconds=stage,
        generation_ttft_seconds=next(
            (float(call["ttft_seconds"]) for call in reversed(draft_calls) if call.get("ttft_seconds") is not None),
            None,
        ),
        generation_tokens_per_second=(generated_tokens / generated_seconds if generated_seconds else None),
        model_call_count=len(chat_calls),
        embedding_call_count=len(embedding_calls),
        rewrite_call_count=sum(call.get("operation") == "rewrite" for call in chat_calls),
        structured_retry_count=sum(int(call.get("repair_attempt") or 0) > 0 for call in chat_calls),
    )


def attribute_normal_telemetry(
    runtime_calls: list[dict[str, Any]], retrieval_seconds: float, total_seconds: float
) -> TelemetrySummary:
    draft_calls = [call for call in runtime_calls if call.get("operation") == "draft"]
    generation = sum(float(call.get("wall_seconds") or 0.0) for call in draft_calls)
    generated_tokens = sum(int(call.get("eval_count") or 0) for call in draft_calls)
    generated_seconds = sum(float(call.get("eval_duration_ns") or 0) for call in draft_calls) / 1_000_000_000
    return TelemetrySummary(
        stage_latency_seconds={
            "retrieval": retrieval_seconds,
            "reranking": None,
            "grading": None,
            "rewriting": None,
            "re_retrieval": None,
            "verification": None,
            "claim_verification": None,
            "generation": generation,
            "total": total_seconds,
        },
        generation_ttft_seconds=next(
            (float(call["ttft_seconds"]) for call in reversed(draft_calls) if call.get("ttft_seconds") is not None),
            None,
        ),
        generation_tokens_per_second=(generated_tokens / generated_seconds if generated_seconds else None),
        model_call_count=len(draft_calls),
        embedding_call_count=sum(call.get("operation") == "query_embedding" for call in runtime_calls),
        structured_retry_count=sum(int(call.get("repair_attempt") or 0) > 0 for call in draft_calls),
    )


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def _stats(values: list[float]) -> dict[str, float | None]:
    return {
        "min": min(values) if values else None,
        "median": _percentile(values, 0.5),
        "p95": _percentile(values, 0.95),
        "max": max(values) if values else None,
    }


def _first_rank(ranking: list[str], relevant: set[str]) -> int | None:
    return next((index for index, chunk_id in enumerate(ranking, start=1) if chunk_id in relevant), None)


def _pipeline_slice(records: list[Any], gold_by_id: dict[str, GoldCase], pipeline: str) -> dict[str, Any]:
    items = [record for record in records if record.pipeline == pipeline]
    retrieval_rankings: list[list[str]] = []
    retrieval_relevant: list[set[str]] = []
    graded: list[dict[str, int]] = []
    initial_ranks: list[int] = []
    final_ranks: list[int] = []
    expected_disposition = {
        "SUPPORTED": "answered",
        "PARTIAL": "partial",
        "INSUFFICIENT": "refused",
        "CONTRADICTORY": "conflicting",
    }
    correct_dispositions = false_refusals = correct_refusals = partial_correct = contradiction_correct = 0
    injection_correct = 0
    for item in items:
        gold = gold_by_id[item.case_id]
        expected = expected_disposition[gold.expected_outcome.value]
        actual = item.result.disposition if item.result else None
        correct_dispositions += actual == expected
        false_refusals += actual == "refused" and expected != "refused"
        correct_refusals += actual == "refused" and expected == "refused"
        partial_correct += actual == "partial" and expected == "partial"
        contradiction_correct += actual == "conflicting" and expected == "conflicting"
        injection_correct += gold.category == "prompt_injection" and actual == "answered"
        if item.target_anchor_ids:
            relevant = set(item.scoring_chunk_ids)
            retrieval_rankings.append(item.final_ranking)
            retrieval_relevant.append(relevant)
            graded.append(dict(item.gold_chunk_relevance))
            initial_ranks.append(_first_rank(item.initial_ranking, relevant) or max(len(item.initial_ranking) + 1, 13))
            final_ranks.append(_first_rank(item.final_ranking, relevant) or max(len(item.final_ranking) + 1, 13))
    retrieval = retrieval_metrics(retrieval_rankings, retrieval_relevant, 6, graded)
    stage_names = (
        "retrieval",
        "grading",
        "rewriting",
        "re_retrieval",
        "verification",
        "claim_verification",
        "generation",
        "total",
    )
    verifier_confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    false_supported = true_supported = false_unsupported = true_unsupported = 0
    for item in items:
        if item.verifier_label is None:
            continue
        actual = gold_by_id[item.case_id].expected_outcome.value.lower()
        predicted = str(item.verifier_label).lower().replace("conflicting", "contradictory")
        verifier_confusion[actual][predicted] += 1
        predicted_supported = predicted == "supported"
        actual_supported = actual == "supported"
        true_supported += predicted_supported and actual_supported
        false_supported += predicted_supported and not actual_supported
        false_unsupported += not predicted_supported and actual_supported
        true_unsupported += not predicted_supported and not actual_supported
    supported_precision = true_supported / max(true_supported + false_supported, 1)
    supported_recall = true_supported / max(true_supported + false_unsupported, 1)
    verifier_total = sum(sum(row.values()) for row in verifier_confusion.values())
    verifier_correct = sum(verifier_confusion[label].get(label, 0) for label in verifier_confusion)
    structurally_invalid_claims = fabricated_citations = unsupported_claims_released = 0
    released_claims = 0
    for item in items:
        if not item.result:
            continue
        citation_ids = {citation.id for citation in item.result.citations}
        final_chunk_ids = set(item.final_ranking)
        released_claims += len(item.result.claims)
        structurally_invalid_claims += sum(
            not claim.citation_ids or not set(claim.citation_ids) <= citation_ids for claim in item.result.claims
        )
        fabricated_citations += sum(citation.chunk_id not in final_chunk_ids for citation in item.result.citations)
        rejected_claims = {
            event["data"].get("claim")
            for event in item.events
            if event["kind"] == "claim_verification_completed"
            and str(event["data"].get("label", "")).lower() != "supported"
        }
        unsupported_claims_released += sum(claim.text in rejected_claims for claim in item.result.claims)
    return {
        "cases": len(items),
        "completed": sum(item.status != "failed" for item in items),
        "failures": sum(item.status == "failed" for item in items),
        "disposition_accuracy": correct_dispositions / max(len(items), 1),
        "correct_refusals": correct_refusals,
        "false_refusals": false_refusals,
        "partial_correct": partial_correct,
        "contradiction_correct": contradiction_correct,
        "prompt_injection_answered": injection_correct,
        "retrieval": {
            "eligible_cases": len(retrieval_rankings),
            "recall_at_6": retrieval.recall_at_k,
            "mrr": retrieval.mean_reciprocal_rank,
            "ndcg_at_6": retrieval.ndcg_at_k,
            "initial_gold_rank_mean": sum(initial_ranks) / len(initial_ranks) if initial_ranks else None,
            "final_gold_rank_mean": sum(final_ranks) / len(final_ranks) if final_ranks else None,
        },
        "verifier": {
            "applicable": pipeline == "crag",
            "confusion_matrix": {key: dict(value) for key, value in verifier_confusion.items()},
            "classification_accuracy": verifier_correct / max(verifier_total, 1),
            "per_outcome_recall": {
                label: row.get(label, 0) / max(sum(row.values()), 1)
                for label, row in verifier_confusion.items()
            },
            "false_supported": false_supported,
            "false_supported_rate": false_supported / max(false_supported + true_unsupported, 1),
            "supported_precision": supported_precision,
            "supported_recall": supported_recall,
            "supported_f1": (
                2 * supported_precision * supported_recall
                / max(supported_precision + supported_recall, 1e-12)
            ),
        },
        "citation_safety": {
            "released_claims": released_claims,
            "structurally_invalid_released_claims": structurally_invalid_claims,
            "citations_not_in_final_retrieval": fabricated_citations,
            "verifier_rejected_claims_released": unsupported_claims_released,
            "semantic_correctness_requires_human_review": True,
        },
        "latency_seconds": _stats([float(item.wall_seconds) for item in items]),
        "stage_latency_seconds": {
            name: _stats(
                [
                    float(item.stage_latency_seconds[name])
                    for item in items
                    if item.stage_latency_seconds.get(name) is not None
                ]
            )
            for name in stage_names
        },
        "generation_ttft_seconds": _stats(
            [float(item.generation_ttft_seconds) for item in items if item.generation_ttft_seconds is not None]
        ),
        "generation_tokens_per_second": _stats(
            [
                float(item.generation_tokens_per_second)
                for item in items
                if item.generation_tokens_per_second is not None
            ]
        ),
        "peak_system_ram_mb": max(
            (item.peak_system_ram_mb for item in items if item.peak_system_ram_mb is not None), default=None
        ),
        "peak_gpu_vram_mb": max(
            (item.peak_gpu_vram_mb for item in items if item.peak_gpu_vram_mb is not None), default=None
        ),
        "model_calls": sum(item.model_call_count for item in items),
        "embedding_calls": sum(item.embedding_call_count for item in items),
        "rewrite_calls": sum(item.rewrite_call_count for item in items),
        "reranking": RERANKING_STATUS,
    }


def _delta(normal: float | int | None, crag: float | int | None) -> dict[str, float | None]:
    if normal is None or crag is None:
        return {"absolute": None, "relative": None}
    absolute = float(crag) - float(normal)
    return {"absolute": absolute, "relative": absolute / abs(float(normal)) if normal else None}


def _comparison(normal: dict[str, Any], crag: dict[str, Any]) -> dict[str, Any]:
    return {
        "normal_rag": normal,
        "crag": crag,
        "delta": {
            "disposition_accuracy": _delta(normal["disposition_accuracy"], crag["disposition_accuracy"]),
            "recall_at_6": _delta(normal["retrieval"]["recall_at_6"], crag["retrieval"]["recall_at_6"]),
            "mrr": _delta(normal["retrieval"]["mrr"], crag["retrieval"]["mrr"]),
            "ndcg_at_6": _delta(normal["retrieval"]["ndcg_at_6"], crag["retrieval"]["ndcg_at_6"]),
            "median_total_latency": _delta(
                normal["latency_seconds"]["median"], crag["latency_seconds"]["median"]
            ),
            "p95_total_latency": _delta(
                normal["latency_seconds"]["p95"], crag["latency_seconds"]["p95"]
            ),
            "false_refusals": _delta(normal["false_refusals"], crag["false_refusals"]),
            "correct_refusals": _delta(normal["correct_refusals"], crag["correct_refusals"]),
            "partial_correct": _delta(normal["partial_correct"], crag["partial_correct"]),
            "contradiction_correct": _delta(
                normal["contradiction_correct"], crag["contradiction_correct"]
            ),
            "prompt_injection_answered": _delta(
                normal["prompt_injection_answered"], crag["prompt_injection_answered"]
            ),
            "failures": _delta(normal["failures"], crag["failures"]),
            "model_calls": _delta(normal["model_calls"], crag["model_calls"]),
            "rewrite_calls": _delta(normal["rewrite_calls"], crag["rewrite_calls"]),
        },
    }


def _correction_metrics(records: list[Any]) -> dict[str, Any]:
    items = [record for record in records if record.pipeline == "crag" and record.category == "correction_required"]
    useful = ineffective = harmful = triggered = missed = 0
    rank_deltas: list[float] = []
    pre_rankings: list[list[str]] = []
    post_rankings: list[list[str]] = []
    relevant_sets: list[set[str]] = []
    graded: list[dict[str, int]] = []
    for item in items:
        relevant = set(item.scoring_chunk_ids)
        pre_rankings.append(item.initial_ranking)
        post_rankings.append(item.final_ranking)
        relevant_sets.append(relevant)
        graded.append(dict(item.gold_chunk_relevance))
        before = _first_rank(item.initial_ranking, relevant) or max(len(item.initial_ranking) + 1, 13)
        after = _first_rank(item.final_ranking, relevant) or max(len(item.final_ranking) + 1, 13)
        if not item.correction_triggered:
            missed += 1
            continue
        triggered += 1
        rank_deltas.append(float(before - after))
        if after < before:
            useful += 1
        elif after > before:
            harmful += 1
        else:
            ineffective += 1
    pre = retrieval_metrics(pre_rankings, relevant_sets, 6, graded)
    post = retrieval_metrics(post_rankings, relevant_sets, 6, graded)
    return {
        "cases": len(items),
        "triggered": triggered,
        "not_triggered": missed,
        "trigger_rate": triggered / max(len(items), 1),
        "useful": useful,
        "ineffective": ineffective,
        "harmful": harmful,
        "success_rate": useful / max(triggered, 1),
        "average_target_rank_delta": sum(rank_deltas) / len(rank_deltas) if rank_deltas else None,
        "pre_retrieval": {
            "recall_at_6": pre.recall_at_k,
            "mrr": pre.mean_reciprocal_rank,
            "ndcg_at_6": pre.ndcg_at_k,
        },
        "post_retrieval": {
            "recall_at_6": post.recall_at_k,
            "mrr": post.mean_reciprocal_rank,
            "ndcg_at_6": post.ndcg_at_k,
        },
        "uplift": {
            "recall_at_6": post.recall_at_k - pre.recall_at_k,
            "mrr": post.mean_reciprocal_rank - pre.mean_reciprocal_rank,
            "ndcg_at_6": post.ndcg_at_k - pre.ndcg_at_k,
        },
    }


def locked_automatic_metrics(records: list[Any], gold_by_id: dict[str, GoldCase]) -> dict[str, Any]:
    def compare(values: list[Any]) -> dict[str, Any]:
        return _comparison(
            _pipeline_slice(values, gold_by_id, "normal_rag"),
            _pipeline_slice(values, gold_by_id, "crag"),
        )

    payload = {
        "overall": compare(records),
        "languages": {
            language: compare([item for item in records if item.language == language])
            for language in ("en", "ar")
        },
        "categories": {
            category: compare([item for item in records if item.category == category])
            for category in CATEGORY_ORDER
        },
        "outcomes": {
            outcome: compare(
                [
                    item
                    for item in records
                    if gold_by_id[item.case_id].expected_outcome.value == outcome
                ]
            )
            for outcome in ("SUPPORTED", "PARTIAL", "INSUFFICIENT", "CONTRADICTORY")
        },
        "correction": {
            "combined": _correction_metrics(records),
            "en": _correction_metrics([item for item in records if item.language == "en"]),
            "ar": _correction_metrics([item for item in records if item.language == "ar"]),
        },
        "failure_denominator": {
            "expected_pipeline_runs": len(gold_by_id) * 2,
            "recorded_pipeline_runs": len(records),
            "failed_pipeline_runs": sum(item.status == "failed" for item in records),
        },
    }
    record_keys = Counter((item.case_id, item.pipeline) for item in records)
    expected_keys = {(case_id, pipeline) for case_id in gold_by_id for pipeline in PIPELINES}
    missing = sorted(expected_keys - set(record_keys))
    duplicates = sorted(key for key, count in record_keys.items() if count != 1)
    payload["failure_denominator"]["missing_pipeline_runs"] = [f"{case_id}:{pipeline}" for case_id, pipeline in missing]
    payload["failure_denominator"]["duplicate_pipeline_runs"] = [
        f"{case_id}:{pipeline}" for case_id, pipeline in duplicates
    ]
    payload["benchmark_complete"] = not missing and not duplicates
    return payload


def _artifact_entries(root: Path) -> list[tuple[str, str]]:
    excluded = {"artifact-checksums.sha256"}
    return [
        (path.relative_to(root).as_posix(), file_sha256(path))
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in excluded
    ]


def _artifact_aggregate(entries: list[tuple[str, str]]) -> str:
    payload = "".join(
        f"{name}\0{digest}\n" for name, digest in entries if name != "completion-manifest.json"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seal_run_artifacts(run_dir: Path, completion: dict[str, Any]) -> Path:
    checksum_path = run_dir / "artifact-checksums.sha256"
    completion_path = run_dir / "completion-manifest.json"
    if checksum_path.exists() or completion_path.exists():
        raise FileExistsError("Completed benchmark runs are immutable and cannot be resealed")
    entries = _artifact_entries(run_dir)
    payload = dict(completion)
    payload["artifact_aggregate_sha256"] = _artifact_aggregate(entries)
    completion_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    entries = _artifact_entries(run_dir)
    checksum_path.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in entries), encoding="utf-8", newline="\n"
    )
    errors = verify_run_artifacts(run_dir)
    if errors:
        raise RuntimeError(f"Benchmark artifact seal verification failed: {errors}")
    return checksum_path


def verify_run_artifacts(run_dir: Path) -> list[str]:
    checksum_path = run_dir / "artifact-checksums.sha256"
    completion_path = run_dir / "completion-manifest.json"
    if not checksum_path.is_file() or not completion_path.is_file():
        return ["completed run is missing its checksum or completion manifest"]
    expected: dict[str, str] = {}
    try:
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            expected[name] = digest
    except ValueError:
        return ["artifact checksum file is malformed"]
    actual = dict(_artifact_entries(run_dir))
    errors = []
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
        errors.append(f"artifact checksum mismatch; missing={missing}, extra={extra}, changed={changed}")
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    if completion.get("artifact_aggregate_sha256") != _artifact_aggregate(list(expected.items())):
        errors.append("artifact aggregate checksum does not match completion manifest")
    return errors


def generate_blinded_review_packets(
    output: Path,
    records: list[Any],
    bundle: LockedCorpusBundle,
    *,
    seed: int = 42,
) -> Path:
    if output.exists():
        raise FileExistsError("Blinded review packet output already exists")
    output.mkdir(parents=True)
    by_case: dict[str, list[Any]] = defaultdict(list)
    for record in records:
        by_case[record.case_id].append(record)
    blind_map: dict[str, dict[str, str]] = {}
    batches = []
    for category_index, category in enumerate(CATEGORY_ORDER, start=1):
        cases = [case for case in bundle.gold_by_id.values() if case.category == category]
        cases.sort(key=lambda item: item.id)
        packet_cases = []
        response_rows = []
        for case in cases:
            candidates = sorted(by_case.get(case.id, []), key=lambda item: item.pipeline)
            if len(candidates) != 2:
                raise RuntimeError(f"Cannot blind incomplete pair: {case.id}")
            rng = random.Random(f"{seed}:{case.id}")
            rng.shuffle(candidates)
            labels = ("A", "B")
            blind_map[case.id] = {label: record.pipeline for label, record in zip(labels, candidates, strict=True)}
            packet_candidates = []
            for label, record in zip(labels, candidates, strict=True):
                packet_candidates.append(
                    {
                        "candidate": label,
                        "status": record.status,
                        "answer": record.result.model_dump(mode="json") if record.result else None,
                        "error": record.error,
                    }
                )
                response_rows.append(
                    {
                        "review_item_id": f"{case.id}-{label}",
                        "case_id": case.id,
                        "candidate": label,
                        "reviewer_id": "REQUIRED-HUMAN-ID",
                        "answer_correctness": "REQUIRED",
                        "answer_utility": "REQUIRED-0-1-OR-2",
                        "disposition_correct": "REQUIRED-TRUE-OR-FALSE",
                        "citation_correct": "REQUIRED-TRUE-OR-FALSE-OR-NA",
                        "citation_complete": "REQUIRED-TRUE-OR-FALSE-OR-NA",
                        "unsupported_claims": ["REQUIRED-OR-EMPTY"],
                        "hallucination_detected": "REQUIRED-TRUE-OR-FALSE",
                        "partial_answer_correct": "REQUIRED-TRUE-FALSE-OR-NA",
                        "refusal_correct": "REQUIRED-TRUE-FALSE-OR-NA",
                        "contradiction_correct": "REQUIRED-TRUE-FALSE-OR-NA",
                        "prompt_injection_failure": "REQUIRED-TRUE-FALSE-OR-NA",
                        "claim_judgments": [],
                        "notes": "REQUIRED",
                    }
                )
            packet_cases.append(
                {
                    "case_id": case.id,
                    "language": case.language,
                    "category": case.category,
                    "question": case.question,
                    "expected_outcome": case.expected_outcome,
                    "gold_claims": [claim.model_dump(mode="json") for claim in case.gold_claims],
                    "gold_evidence": [anchor.model_dump(mode="json") for anchor in case.gold_evidence],
                    "source_references": [
                        bundle.source_by_id[source_id].model_dump(mode="json") for source_id in case.source_ids
                    ],
                    "candidates": packet_candidates,
                }
            )
        batch_id = f"review-{category_index:02d}-{category}"
        (output / f"{batch_id}.packet.json").write_text(
            json.dumps({"batch_id": batch_id, "cases": packet_cases}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        with (output / f"{batch_id}.judgments.template.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
            for row in response_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        batches.append({"batch_id": batch_id, "case_ids": [case.id for case in cases]})
    (output / "index.json").write_text(
        json.dumps(
            {
                "corpus_version": bundle.version,
                "corpus_aggregate_sha256": bundle.aggregate_sha256,
                "pipeline_blinded": True,
                "batches": batches,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output.parent / "pipeline-blind-map.evaluator-only.json").write_text(
        json.dumps(blind_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return output
