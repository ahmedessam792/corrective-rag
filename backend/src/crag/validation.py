from __future__ import annotations

import argparse
import asyncio
import ctypes
import hashlib
import json
import math
import os
import platform
import random
import shutil
import subprocess
import time
from collections import defaultdict
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from crag.config import Settings
from crag.corpus import (
    apply_review_records,
    audit_corpus,
    compile_runtime_manifest,
    lock_corpus,
    verify_locked_corpus,
)
from crag.database import Database
from crag.domain import AnswerResult, Citation, Claim
from crag.evaluation import BenchmarkCase, audit_manifest, correction_metrics, load_manifest, retrieval_metrics
from crag.ingestion import IngestionService, OllamaEmbedder
from crag.retrieval import HybridRetriever
from crag.runtime import Draft, OllamaRuntime
from crag.workflow import CragWorkflow


class CaseRunRecord(BaseModel):
    case_id: str
    language: str
    category: str
    pipeline: Literal["normal_rag", "crag"]
    order: int
    wall_seconds: float
    result: AnswerResult | None = None
    status: str
    error: str | None = None
    initial_ranking: list[str] = Field(default_factory=list)
    final_ranking: list[str] = Field(default_factory=list)
    dense_ranking: list[str] = Field(default_factory=list)
    lexical_ranking: list[str] = Field(default_factory=list)
    relevant_chunk_ids: list[str] = Field(default_factory=list)
    invalid_draft_citations: int = 0
    events: list[dict[str, Any]] = Field(default_factory=list)
    runtime_calls: list[dict[str, Any]] = Field(default_factory=list)


class ResourceSample(BaseModel):
    elapsed_seconds: float
    system_ram_used_mb: float | None = None
    gpu_vram_used_mb: float | None = None


class ClaimJudgment(BaseModel):
    claim: str
    actual_supported: bool
    citation_correct: bool | None = None
    predicted_supported: bool | None = None
    verifier_label: str | None = None
    notes: str | None = None


class HumanJudgment(BaseModel):
    case_id: str
    pipeline: Literal["normal_rag", "crag"]
    reviewer: str = Field(min_length=1)
    disposition_correct: bool
    answer_utility: int = Field(ge=0, le=2)
    claims: list[ClaimJudgment] = Field(default_factory=list)
    adjudicator: str | None = None
    notes: str | None = None


class OperationalGate(BaseModel):
    passed: bool
    evidence: str = Field(min_length=1)
    limitation: bool = False


class OperationalEvidence(BaseModel):
    real_runtime_smoke: OperationalGate
    cancellation: OperationalGate
    restart_recovery: OperationalGate
    prompt_injection: OperationalGate
    ocr: OperationalGate


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong),
        ("memory_load", ctypes.c_ulong),
        ("total_physical", ctypes.c_ulonglong),
        ("available_physical", ctypes.c_ulonglong),
        ("total_page_file", ctypes.c_ulonglong),
        ("available_page_file", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong),
        ("available_virtual", ctypes.c_ulonglong),
        ("available_extended_virtual", ctypes.c_ulonglong),
    ]


def _system_ram_used_mb() -> float | None:
    if os.name != "nt":
        return None
    status = _MemoryStatus()
    status.length = ctypes.sizeof(_MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return (status.total_physical - status.available_physical) / (1024 * 1024)


def _command(args: list[str]) -> str | None:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        ).stdout.strip() or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _ollama_command(*args: str) -> list[str] | None:
    executable = shutil.which("ollama")
    if not executable and os.name == "nt":
        candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        if candidate.is_file():
            executable = str(candidate)
    return [executable, *args] if executable else None


def _gpu_vram_used_mb() -> float | None:
    output = _command([
        "nvidia-smi",
        "--query-gpu=memory.used",
        "--format=csv,noheader,nounits",
    ])
    if not output:
        return None
    with suppress(ValueError):
        return max(float(line.strip()) for line in output.splitlines() if line.strip())
    return None


class ResourceSampler:
    def __init__(self, interval_seconds: float = 0.5):
        self.interval_seconds = interval_seconds
        self.samples: list[ResourceSample] = []
        self._stop = asyncio.Event()
        self._started = 0.0

    async def run(self) -> None:
        self._started = time.monotonic()
        while not self._stop.is_set():
            ram = _system_ram_used_mb()
            vram = _gpu_vram_used_mb()
            self.samples.append(
                ResourceSample(
                    elapsed_seconds=time.monotonic() - self._started,
                    system_ram_used_mb=ram,
                    gpu_vram_used_mb=vram,
                )
            )
            with suppress(TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)

    def stop(self) -> None:
        self._stop.set()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _environment_snapshot(settings: Settings) -> dict[str, Any]:
    version_command = _ollama_command("--version")
    ps_command = _ollama_command("ps")
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "git_head": _command(["git", "rev-parse", "HEAD"]),
        "git_status": _command(["git", "status", "--short"]),
        "nvidia_smi": _command(["nvidia-smi"]),
        "ollama_version": _command(version_command) if version_command else None,
        "ollama_ps": _command(ps_command) if ps_command else None,
        "runtime": {
            "url": settings.ollama_url,
            "chat_model": settings.chat_model,
            "embed_model": settings.embed_model,
            "context_size": settings.ollama_context_size,
            "output_tokens": settings.ollama_output_tokens,
            "seed": settings.ollama_seed,
            "gpu_layers": settings.ollama_gpu_layers,
            "keep_alive": settings.ollama_keep_alive,
            "max_corrections": settings.max_corrections,
            "context_chunks": settings.context_chunks,
        },
    }


async def _ollama_model_snapshot(settings: Settings) -> dict[str, Any]:
    base_url = settings.ollama_url.rstrip("/")
    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        tags_response = await client.get(f"{base_url}/api/tags")
        tags_response.raise_for_status()
        models = {
            item.get("name"): {
                "digest": item.get("digest"),
                "size": item.get("size"),
                "details": item.get("details"),
            }
            for item in tags_response.json().get("models", [])
        }
        details: dict[str, Any] = {}
        for model in (settings.chat_model, settings.embed_model):
            response = await client.post(f"{base_url}/api/show", json={"model": model})
            response.raise_for_status()
            payload = response.json()
            details[model] = {
                "tag": models.get(model),
                "details": payload.get("details"),
                "model_info": payload.get("model_info"),
                "capabilities": payload.get("capabilities"),
                "parameters": payload.get("parameters"),
            }
        return details


def _runtime(settings: Settings) -> OllamaRuntime:
    return OllamaRuntime(
        settings.ollama_url,
        settings.chat_model,
        settings.embed_model,
        context_size=settings.ollama_context_size,
        output_tokens=settings.ollama_output_tokens,
        seed=settings.ollama_seed,
        gpu_layers=settings.ollama_gpu_layers,
        keep_alive=settings.ollama_keep_alive,
        timeout_seconds=settings.ollama_timeout_seconds,
        repair_attempts=settings.structured_repair_attempts,
    )


def _embedder(settings: Settings) -> OllamaEmbedder:
    return OllamaEmbedder(
        settings.ollama_url,
        settings.embed_model,
        keep_alive=settings.ollama_keep_alive,
        timeout_seconds=settings.ollama_timeout_seconds,
        gpu_layers=settings.ollama_gpu_layers,
    )


def _citations(ids: set[str], evidence: list[Any]) -> list[Citation]:
    return [
        Citation(
            id=item.citation_id,
            document_id=item.document_id,
            filename=item.filename,
            chunk_id=item.id,
            passage=item.text,
            anchor=item.anchor,
        )
        for item in evidence
        if item.citation_id in ids
    ]


async def _normal_rag(
    case: BenchmarkCase,
    retriever: HybridRetriever,
    runtime: OllamaRuntime,
    workspace_id: str,
    relevant_ids: list[str],
    order: int,
    context_chunks: int,
) -> CaseRunRecord:
    started = time.monotonic()
    try:
        trace = await asyncio.to_thread(retriever.retrieve_with_trace, workspace_id, case.question, 12)
        embedding_calls = retriever.embedder.drain_telemetry()
        selected = trace.results[:context_chunks]
        draft: Draft = await runtime.draft(case.question, selected)
        allowed = {item.citation_id for item in selected}
        claims: list[Claim] = []
        invalid = 0
        for claim in draft.claims:
            if claim.citation_ids and set(claim.citation_ids) <= allowed:
                claims.append(claim)
            else:
                invalid += 1
        needed = {citation_id for claim in claims for citation_id in claim.citation_ids}
        if claims:
            result = AnswerResult(
                disposition="answered",
                summary=" ".join(claim.text for claim in claims),
                claims=claims,
                citations=_citations(needed, selected),
            )
            status = "completed"
        else:
            result = AnswerResult(
                disposition="refused",
                summary="No reliable answer found.",
                refusal_reason="The normal-RAG draft contained no structurally valid cited claim.",
            )
            status = "refused"
        return CaseRunRecord(
            case_id=case.id,
            language=case.language,
            category=case.category,
            pipeline="normal_rag",
            order=order,
            wall_seconds=time.monotonic() - started,
            result=result,
            status=status,
            initial_ranking=trace.fused_ranking,
            final_ranking=trace.fused_ranking,
            dense_ranking=trace.dense_ranking,
            lexical_ranking=trace.lexical_ranking,
            relevant_chunk_ids=relevant_ids,
            invalid_draft_citations=invalid,
            runtime_calls=[*embedding_calls, *[item.model_dump() for item in runtime.drain_telemetry()]],
        )
    except Exception as exc:
        return CaseRunRecord(
            case_id=case.id,
            language=case.language,
            category=case.category,
            pipeline="normal_rag",
            order=order,
            wall_seconds=time.monotonic() - started,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            relevant_chunk_ids=relevant_ids,
            runtime_calls=[
                *retriever.embedder.drain_telemetry(),
                *[item.model_dump() for item in runtime.drain_telemetry()],
            ],
        )


async def _crag(
    case: BenchmarkCase,
    database: Database,
    workflow: CragWorkflow,
    workspace_id: str,
    relevant_ids: list[str],
    order: int,
) -> CaseRunRecord:
    started = time.monotonic()
    run = database.create_run(str(uuid4()), workspace_id, case.question)
    await workflow.execute(run.id)
    completed = database.get_run(run.id)
    events = [event.model_dump(mode="json") for event in database.list_events(run.id)]
    retrieval_events = [event for event in events if event["kind"] == "retrieval_completed"]
    runtime_calls = [event["data"] for event in events if event["kind"] == "runtime_call_completed"]
    initial = retrieval_events[0]["data"].get("fused_ranking", []) if retrieval_events else []
    final = retrieval_events[-1]["data"].get("fused_ranking", []) if retrieval_events else []
    return CaseRunRecord(
        case_id=case.id,
        language=case.language,
        category=case.category,
        pipeline="crag",
        order=order,
        wall_seconds=time.monotonic() - started,
        result=completed.result if completed else None,
        status=completed.status if completed else "failed",
        error=completed.error if completed else "Persisted run disappeared.",
        initial_ranking=initial,
        final_ranking=final,
        dense_ranking=retrieval_events[0]["data"].get("dense_ranking", []) if retrieval_events else [],
        lexical_ranking=retrieval_events[0]["data"].get("lexical_ranking", []) if retrieval_events else [],
        relevant_chunk_ids=relevant_ids,
        events=events,
        runtime_calls=runtime_calls,
    )


def _gold_chunk_ids(database: Database, workspace_id: str, case: BenchmarkCase) -> list[str]:
    rows = database.chunk_rows(workspace_id)
    ids: set[str] = set()
    for gold in case.gold_evidence:
        fixture = gold.fixture or case.fixture
        for row in rows:
            if row["filename"] != fixture or gold.text_contains not in row["text"]:
                continue
            anchor = database.row_to_chunk(row).anchor
            if gold.page is not None and anchor.page != gold.page:
                continue
            if gold.paragraph is not None:
                start = anchor.paragraph_start
                end = anchor.paragraph_end if anchor.paragraph_end is not None else start
                if start is None or end is None or not start <= gold.paragraph <= end:
                    continue
            ids.add(row["id"])
    return sorted(ids)


async def _cold_start_samples(settings: Settings, count: int = 3) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    schema = {
        "type": "object",
        "properties": {"ready": {"type": "boolean"}},
        "required": ["ready"],
    }
    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        for index in range(count):
            await client.post(
                f"{settings.ollama_url.rstrip('/')}/api/generate",
                json={"model": settings.chat_model, "keep_alive": 0},
            )
            started = time.monotonic()
            response = await client.post(
                f"{settings.ollama_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.chat_model,
                    "stream": False,
                    "format": schema,
                    "keep_alive": 0,
                    "think": False,
                    "options": {
                        "temperature": 0,
                        "seed": settings.ollama_seed,
                        "num_ctx": settings.ollama_context_size,
                        "num_gpu": settings.ollama_gpu_layers,
                        "num_predict": 16,
                    },
                    "messages": [{"role": "user", "content": "Return {\"ready\": true}."}],
                },
            )
            response.raise_for_status()
            payload = response.json()
            samples.append(
                {
                    "sample": index + 1,
                    "wall_seconds": time.monotonic() - started,
                    "load_duration_ns": payload.get("load_duration"),
                    "total_duration_ns": payload.get("total_duration"),
                }
            )
    return samples


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _automatic_metrics(records: list[CaseRunRecord]) -> dict[str, Any]:
    grouped: dict[str, list[CaseRunRecord]] = defaultdict(list)
    for record in records:
        grouped[record.pipeline].append(record)
    payload: dict[str, Any] = {}
    for pipeline, items in grouped.items():
        rankings = [item.final_ranking for item in items if item.relevant_chunk_ids]
        relevant = [set(item.relevant_chunk_ids) for item in items if item.relevant_chunk_ids]
        latency = [item.wall_seconds for item in items if item.status != "failed"]
        retrieval = retrieval_metrics(rankings, relevant, 6)
        payload[pipeline] = {
            "cases": len(items),
            "failures": sum(item.status == "failed" for item in items),
            "invalid_draft_citations": sum(item.invalid_draft_citations for item in items),
            "retrieval_at_6": {
                "recall": retrieval.recall_at_k,
                "mrr": retrieval.mean_reciprocal_rank,
                "ndcg": retrieval.ndcg_at_k,
            },
            "latency_seconds": {
                "median": _percentile(latency, 0.5),
                "p95": _percentile(latency, 0.95),
            },
        }
        payload[pipeline]["languages"] = {}
        for language in ("en", "ar"):
            language_items = [item for item in items if item.language == language]
            language_rankings = [item.final_ranking for item in language_items if item.relevant_chunk_ids]
            language_relevant = [set(item.relevant_chunk_ids) for item in language_items if item.relevant_chunk_ids]
            language_latency = [item.wall_seconds for item in language_items if item.status != "failed"]
            language_retrieval = retrieval_metrics(language_rankings, language_relevant, 6)
            payload[pipeline]["languages"][language] = {
                "cases": len(language_items),
                "failures": sum(item.status == "failed" for item in language_items),
                "retrieval_at_6": {
                    "recall": language_retrieval.recall_at_k,
                    "mrr": language_retrieval.mean_reciprocal_rank,
                    "ndcg": language_retrieval.ndcg_at_k,
                },
                "latency_seconds": {
                    "median": _percentile(language_latency, 0.5),
                    "p95": _percentile(language_latency, 0.95),
                },
            }
    correction_items = [
        item
        for item in grouped.get("crag", [])
        if item.category == "correction_required" and item.relevant_chunk_ids
    ]
    if correction_items:
        metrics = correction_metrics(
            [item.initial_ranking for item in correction_items],
            [item.final_ranking for item in correction_items],
            [set(item.relevant_chunk_ids) for item in correction_items],
            6,
        )
        payload["correction"] = {
            "improved": metrics.improved,
            "unchanged": metrics.unchanged,
            "regressed": metrics.regressed,
            "pre": {
                "recall": metrics.pre_retrieval.recall_at_k,
                "mrr": metrics.pre_retrieval.mean_reciprocal_rank,
                "ndcg": metrics.pre_retrieval.ndcg_at_k,
            },
            "post": {
                "recall": metrics.post_retrieval.recall_at_k,
                "mrr": metrics.post_retrieval.mean_reciprocal_rank,
                "ndcg": metrics.post_retrieval.ndcg_at_k,
            },
        }
        payload["correction"]["languages"] = {}
        for language in ("en", "ar"):
            language_items = [item for item in correction_items if item.language == language]
            if not language_items:
                continue
            language_metrics = correction_metrics(
                [item.initial_ranking for item in language_items],
                [item.final_ranking for item in language_items],
                [set(item.relevant_chunk_ids) for item in language_items],
                6,
            )
            payload["correction"]["languages"][language] = {
                "improved": language_metrics.improved,
                "unchanged": language_metrics.unchanged,
                "regressed": language_metrics.regressed,
                "pre_recall_at_6": language_metrics.pre_retrieval.recall_at_k,
                "post_recall_at_6": language_metrics.post_retrieval.recall_at_k,
                "pre_mrr": language_metrics.pre_retrieval.mean_reciprocal_rank,
                "post_mrr": language_metrics.post_retrieval.mean_reciprocal_rank,
            }
    return payload


def _read_jsonl(path: Path, model: type[BaseModel]) -> list[Any]:
    values: list[Any] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            values.append(model.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"Invalid record at {path}:{line_number}: {exc}") from exc
    return values


def _judgment_metrics(values: list[HumanJudgment]) -> dict[str, Any]:
    claims = [claim for value in values for claim in value.claims]
    released = [claim for claim in claims if claim.predicted_supported is not False]
    verifier = [claim for claim in claims if claim.predicted_supported is not None]
    actual_supported = sum(claim.actual_supported for claim in released)
    citations = [claim for claim in released if claim.citation_correct is not None]
    false_supported = sum(claim.predicted_supported is True and not claim.actual_supported for claim in verifier)
    unsupported_actual = sum(not claim.actual_supported for claim in verifier)
    true_supported = sum(claim.predicted_supported is True and claim.actual_supported for claim in verifier)
    false_unsupported = sum(claim.predicted_supported is False and claim.actual_supported for claim in verifier)
    precision = true_supported / max(true_supported + false_supported, 1)
    recall = true_supported / max(true_supported + false_unsupported, 1)
    return {
        "cases": len(values),
        "grounded_claim_rate": actual_supported / len(released) if released else 1.0,
        "unsupported_claims_released": sum(not claim.actual_supported for claim in released),
        "unsupported_claim_rate": sum(not claim.actual_supported for claim in released) / max(len(released), 1),
        "citation_correctness": (
            sum(bool(claim.citation_correct) for claim in citations) / len(citations) if citations else 1.0
        ),
        "disposition_accuracy": sum(value.disposition_correct for value in values) / max(len(values), 1),
        "mean_answer_utility": sum(value.answer_utility for value in values) / max(len(values), 1),
        "verifier": {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / max(precision + recall, 1e-12),
            "false_supported": false_supported,
            "false_supported_rate": false_supported / max(unsupported_actual, 1),
        },
    }


def _final_metrics(
    records: list[CaseRunRecord],
    judgments: list[HumanJudgment],
    resources: list[ResourceSample],
    operational: OperationalEvidence,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    by_key = {(value.case_id, value.pipeline): value for value in judgments}
    expected = {(value.case_id, value.pipeline) for value in records}
    if set(by_key) != expected:
        missing = sorted(expected - set(by_key))
        extra = sorted(set(by_key) - expected)
        raise ValueError(f"Human judgments do not match predictions; missing={missing}, extra={extra}")

    slices: dict[str, Any] = {}
    for pipeline in ("normal_rag", "crag"):
        pipeline_values = [value for value in judgments if value.pipeline == pipeline]
        slices[pipeline] = {"overall": _judgment_metrics(pipeline_values)}
        for language in ("en", "ar"):
            case_ids = {record.case_id for record in records if record.language == language}
            slices[pipeline][language] = _judgment_metrics(
                [value for value in pipeline_values if value.case_id in case_ids]
            )

    crag = slices["crag"]["overall"]
    baseline = slices["normal_rag"]["overall"]
    baseline_error = baseline["unsupported_claim_rate"]
    required_improvement = 0.10 if baseline_error >= 0.10 else baseline_error * 0.50
    actual_improvement = baseline_error - crag["unsupported_claim_rate"]
    if actual_improvement + 1e-12 < required_improvement:
        failures.append({
            "gate": "normal_rag_vs_crag",
            "evidence": f"Unsupported-claim improvement {actual_improvement:.3f}; required {required_improvement:.3f}.",
            "classification": "CRAG logic/model",
            "next_action": "Inspect paired losses and change only the failing CRAG stage on a new calibration set.",
        })
    utility_drop = baseline["mean_answer_utility"] - crag["mean_answer_utility"]
    if utility_drop > 0.10:
        failures.append({
            "gate": "answer_utility",
            "evidence": f"Mean utility drop {utility_drop:.3f} exceeds 0.10.",
            "classification": "CRAG logic/model",
            "next_action": "Inspect over-refusal and partial-answer losses without weakening support release rules.",
        })
    verifier = crag["verifier"]
    if verifier["false_supported"] or crag["unsupported_claims_released"]:
        failures.append({
            "gate": "verifier_safety",
            "evidence": (
                f"false SUPPORTED={verifier['false_supported']}; "
                f"unsupported released={crag['unsupported_claims_released']}."
            ),
            "classification": "model/CRAG logic",
            "next_action": "Reproduce the exact claim/evidence trace and tighten the verifier before any retest.",
        })
    if verifier["f1"] < 0.85:
        failures.append({
            "gate": "verifier_quality",
            "evidence": f"Verifier support F1={verifier['f1']:.3f}; required at least 0.85.",
            "classification": "model/evaluation",
            "next_action": "Inspect false-unsupported and support-label errors on the calibration set.",
        })
    for language in ("en", "ar"):
        values = slices["crag"][language]
        if values["grounded_claim_rate"] < 1 or values["citation_correctness"] < 1:
            failures.append({
                "gate": f"{language}_safety",
                "evidence": (
                    f"grounded={values['grounded_claim_rate']:.3f}; "
                    f"citations={values['citation_correctness']:.3f}."
                ),
                "classification": "bilingual model/retrieval",
                "next_action": f"Analyze {language} failures independently on the calibration corpus.",
            })
        if values["verifier"]["f1"] < 0.80:
            failures.append({
                "gate": f"{language}_verifier_quality",
                "evidence": f"support F1={values['verifier']['f1']:.3f}; required at least 0.80.",
                "classification": "bilingual model/evaluation",
                "next_action": f"Analyze {language} verifier errors on the calibration corpus.",
            })

    automatic = _automatic_metrics(records)
    correction_records = [
        value
        for value in records
        if value.pipeline == "crag" and value.category == "correction_required" and value.relevant_chunk_ids
    ]
    for language in ("en", "ar"):
        items = [value for value in correction_records if value.language == language]
        if items:
            values = correction_metrics(
                [item.initial_ranking for item in items],
                [item.final_ranking for item in items],
                [set(item.relevant_chunk_ids) for item in items],
                6,
            )
            post_recall = values.post_retrieval.recall_at_k
            if values.improved < 3 or values.regressed > 1 or post_recall < 0.8:
                failures.append({
                    "gate": f"correction_{language}",
                    "evidence": (
                        f"improved={values.improved}, unchanged={values.unchanged}, "
                        f"regressed={values.regressed}, post Recall@6={post_recall:.3f}."
                    ),
                    "classification": "retrieval/correction",
                    "next_action": "Inspect rewrite and rank deltas; test one bounded query or retrieval change.",
                })

    crag_latencies = [
        value.wall_seconds for value in records if value.pipeline == "crag" and value.status != "failed"
    ]
    median_latency = _percentile(crag_latencies, 0.5)
    p95_latency = _percentile(crag_latencies, 0.95)
    if median_latency is None or p95_latency is None or median_latency > 90 or p95_latency > 180:
        failures.append({
            "gate": "target_machine_latency",
            "evidence": f"warm median={median_latency}, p95={p95_latency} seconds.",
            "classification": "model/runtime/hardware",
            "next_action": "Use stage telemetry to test the smallest lower-cost model/configuration change.",
        })
    failed_runs = [value for value in records if value.status == "failed"]
    if failed_runs:
        failures.append({
            "gate": "runtime_stability",
            "evidence": f"{len(failed_runs)} benchmark pipeline runs failed.",
            "classification": "model/runtime",
            "next_action": (
                "Resolve the first reproducible runtime or schema failure before repeating the affected run."
            ),
        })

    optional_limitations: list[str] = []
    for name, gate in operational:
        if gate.passed:
            continue
        if gate.limitation:
            optional_limitations.append(f"{name}: {gate.evidence}")
        else:
            failures.append({
                "gate": name,
                "evidence": gate.evidence,
                "classification": "runtime/CRAG logic",
                "next_action": f"Resolve the recorded {name} failure and rerun that operational gate.",
            })

    if failures:
        verdict = "Validation failed / changes required"
    elif optional_limitations:
        verdict = "Validated with limitations"
    else:
        verdict = "Validated CRAG MVP"
    return {
        "verdict": verdict,
        "human_metrics": slices,
        "automatic_metrics": automatic,
        "resources": {
            "peak_system_ram_mb": max(
                (value.system_ram_used_mb for value in resources if value.system_ram_used_mb is not None),
                default=None,
            ),
            "peak_gpu_vram_mb": max(
                (value.gpu_vram_used_mb for value in resources if value.gpu_vram_used_mb is not None),
                default=None,
            ),
        },
        "operational": operational.model_dump(),
        "limitations": optional_limitations,
        "failures": failures,
    }, failures


def finalize_report(run_dir: Path, judgments_path: Path, operational_path: Path) -> Path:
    records = _read_jsonl(run_dir / "predictions.jsonl", CaseRunRecord)
    judgments = _read_jsonl(judgments_path, HumanJudgment)
    resources = _read_jsonl(run_dir / "resources.jsonl", ResourceSample)
    operational = OperationalEvidence.model_validate_json(operational_path.read_text(encoding="utf-8"))
    report, _ = _final_metrics(records, judgments, resources, operational)
    report_path = run_dir / "final-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {report['verdict']}", "", "## Gate failures", ""]
    if report["failures"]:
        for failure in report["failures"]:
            lines.append(
                f"- **{failure['gate']}** — {failure['evidence']} "
                f"Classification: {failure['classification']}. Next: {failure['next_action']}"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {value}" for value in report["limitations"] or ["None."])
    (run_dir / "final-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


async def run_benchmark(
    manifest_path: Path,
    fixture_dir: Path,
    output_root: Path,
    settings: Settings,
    *,
    allow_provisional: bool = False,
    seed: int = 42,
    case_ids: set[str] | None = None,
) -> Path:
    cases = load_manifest(manifest_path)
    audit = audit_manifest(cases, fixture_dir)
    if not allow_provisional and not audit.acceptance_ready:
        raise RuntimeError(
            "Acceptance manifest is not human-anchored and fixture-complete. Run the audit command for details."
        )
    if audit.missing_fixtures:
        raise RuntimeError(f"Missing fixture files: {', '.join(audit.missing_fixtures)}")
    if case_ids:
        unknown = case_ids - {case.id for case in cases}
        if unknown:
            raise RuntimeError(f"Unknown case IDs: {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case.id in case_ids]

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4().hex[:8]}"
    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    data_dir = output_dir / "workspace"
    database = Database(data_dir / "crag.sqlite3")
    embedder = _embedder(settings)
    runtime = _runtime(settings)
    retriever = HybridRetriever(database, embedder)
    workflow = CragWorkflow(
        database,
        retriever,
        runtime,
        max_corrections=settings.max_corrections,
        context_chunks=settings.context_chunks,
    )
    sampler = ResourceSampler()
    sampler_task = asyncio.create_task(sampler.run())
    records: list[CaseRunRecord] = []
    try:
        health = await runtime.health()
        if not health.ready:
            raise RuntimeError(health.detail)
        environment = _environment_snapshot(settings)
        environment["manifest"] = {"path": str(manifest_path), "sha256": _sha256(manifest_path)}
        environment["models"] = await _ollama_model_snapshot(settings)
        environment["cold_start_samples"] = await _cold_start_samples(settings)

        ingestion = IngestionService(database, data_dir / "uploads", settings.max_upload_mb, embedder)
        index_embedding_calls: list[dict[str, object]] = []
        rng = random.Random(seed)
        for case in cases:
            workspace = database.create_workspace(str(uuid4()), f"validation-{run_id}-{case.id}")
            for fixture in sorted(set(case.fixtures)):
                path = fixture_dir / fixture
                document = await asyncio.to_thread(
                    ingestion.ingest,
                    workspace_id=workspace.id,
                    filename=fixture,
                    content=path.read_bytes(),
                    ocr_requested=path.suffix.lower() == ".pdf",
                )
                if document.status != "ready":
                    raise RuntimeError(
                        f"Fixture ingestion failed for {fixture}: {document.status}: {document.error}"
                    )
            index_embedding_calls.extend(embedder.drain_telemetry())
            relevant_ids = _gold_chunk_ids(database, workspace.id, case)
            if case.gold_evidence and not relevant_ids:
                raise RuntimeError(f"Gold evidence anchors did not resolve for case {case.id}.")
            order = ["normal_rag", "crag"]
            if rng.random() < 0.5:
                order.reverse()
            for position, pipeline in enumerate(order, start=1):
                if pipeline == "normal_rag":
                    record = await _normal_rag(
                        case, retriever, runtime, workspace.id, relevant_ids, position, settings.context_chunks
                    )
                else:
                    record = await _crag(case, database, workflow, workspace.id, relevant_ids, position)
                records.append(record)
                with (output_dir / "predictions.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(record.model_dump_json() + "\n")

        environment["index_embedding_calls"] = index_embedding_calls

        metrics = _automatic_metrics(records)
        ps_command = _ollama_command("ps")
        environment["ollama_ps_after"] = _command(ps_command) if ps_command else None
        (output_dir / "environment.json").write_text(
            json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output_dir / "manifest-audit.json").write_text(
            json.dumps(audit.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output_dir / "automatic-metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        judgment_template = []
        for record in records:
            if record.pipeline == "crag":
                claim_rows = [
                    {
                        "claim": event["data"]["claim"],
                        "actual_supported": None,
                        "citation_correct": None,
                        "predicted_supported": event["data"]["label"] == "supported",
                        "verifier_label": event["data"]["label"],
                    }
                    for event in record.events
                    if event["kind"] == "claim_verification_completed"
                ]
            else:
                claim_rows = [
                    {
                        "claim": claim.text,
                        "actual_supported": None,
                        "citation_correct": None,
                        "predicted_supported": None,
                        "verifier_label": None,
                    }
                    for claim in (record.result.claims if record.result else [])
                ]
            judgment_template.append(
                {
                    "case_id": record.case_id,
                    "pipeline": record.pipeline,
                    "reviewer": "REQUIRED",
                    "disposition_correct": None,
                    "answer_utility": None,
                    "claims": claim_rows,
                }
            )
        with (output_dir / "human-judgments.template.jsonl").open("w", encoding="utf-8") as handle:
            for value in judgment_template:
                handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        (output_dir / "operational-evidence.template.json").write_text(
            json.dumps(
                {
                    name: {"passed": None, "evidence": "REQUIRED", "limitation": name == "ocr"}
                    for name in (
                        "real_runtime_smoke",
                        "cancellation",
                        "restart_recovery",
                        "prompt_injection",
                        "ocr",
                    )
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    finally:
        sampler.stop()
        await sampler_task
        with (output_dir / "resources.jsonl").open("w", encoding="utf-8") as handle:
            for sample in sampler.samples:
                handle.write(sample.model_dump_json() + "\n")
        database.close()
    return output_dir


def _audit_command(args: argparse.Namespace) -> int:
    cases = load_manifest(args.manifest)
    audit = audit_manifest(cases, args.fixtures)
    print(json.dumps(audit.model_dump(), ensure_ascii=False, indent=2))
    return 0 if audit.acceptance_ready else 2


def _run_command(args: argparse.Namespace) -> int:
    settings = Settings(runtime="ollama")
    output = asyncio.run(
        run_benchmark(
            args.manifest,
            args.fixtures,
            args.output,
            settings,
            allow_provisional=args.allow_provisional,
            seed=args.seed,
            case_ids=set(args.case) if args.case else None,
        )
    )
    print(output)
    return 0


def _report_command(args: argparse.Namespace) -> int:
    output = finalize_report(args.run_dir, args.judgments, args.operational)
    print(output)
    return 0


def _corpus_audit_command(args: argparse.Namespace) -> int:
    audit = audit_corpus(args.corpus)
    print(json.dumps(audit.model_dump(), ensure_ascii=False, indent=2))
    return 0 if audit.benchmark_ready else 2


def _corpus_compile_command(args: argparse.Namespace) -> int:
    output = compile_runtime_manifest(args.corpus)
    audit = audit_corpus(args.corpus, verify_lock=False)
    print(json.dumps({"runtime_manifest": str(output), "audit": audit.model_dump()}, ensure_ascii=False, indent=2))
    return 0 if not audit.integrity_errors and not audit.missing_sources else 2


def _corpus_lock_command(args: argparse.Namespace) -> int:
    print(lock_corpus(args.corpus, args.output))
    return 0


def _corpus_apply_reviews_command(args: argparse.Namespace) -> int:
    audit = apply_review_records(args.corpus, args.reviews, args.adjudications)
    print(json.dumps(audit.model_dump(), ensure_ascii=False, indent=2))
    return 0 if not audit.integrity_errors and not audit.case_errors else 2


def _corpus_verify_lock_command(args: argparse.Namespace) -> int:
    errors = verify_locked_corpus(args.corpus)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Local CRAG validation harness")
    commands = result.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Check fixture and human-anchor readiness")
    audit.add_argument("--manifest", type=Path, default=Path("evaluation/pilot_cases.jsonl"))
    audit.add_argument("--fixtures", type=Path, default=Path("evaluation/fixtures"))
    audit.set_defaults(handler=_audit_command)
    run = commands.add_parser("run", help="Run paired normal-RAG and CRAG evaluation")
    run.add_argument("--manifest", type=Path, default=Path("evaluation/pilot_cases.jsonl"))
    run.add_argument("--fixtures", type=Path, default=Path("evaluation/fixtures"))
    run.add_argument("--output", type=Path, default=Path(".evaluation-runs"))
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--allow-provisional", action="store_true")
    run.add_argument("--case", action="append", help="Run only this case ID; repeat as needed")
    run.set_defaults(handler=_run_command)
    report = commands.add_parser("report", help="Issue the evidence-based final verdict")
    report.add_argument("--run-dir", type=Path, required=True)
    report.add_argument("--judgments", type=Path, required=True)
    report.add_argument("--operational", type=Path, required=True)
    report.set_defaults(handler=_report_command)
    corpus_audit = commands.add_parser("corpus-audit", help="Validate a versioned gold corpus")
    corpus_audit.add_argument("--corpus", type=Path, default=Path("evaluation/corpora/crag-gold-v1-draft"))
    corpus_audit.set_defaults(handler=_corpus_audit_command)
    corpus_compile = commands.add_parser(
        "corpus-compile", help="Generate the gold-free runtime manifest and validate its boundary"
    )
    corpus_compile.add_argument("--corpus", type=Path, default=Path("evaluation/corpora/crag-gold-v1-draft"))
    corpus_compile.set_defaults(handler=_corpus_compile_command)
    corpus_lock = commands.add_parser("corpus-lock", help="Create an immutable corpus release")
    corpus_lock.add_argument("--corpus", type=Path, default=Path("evaluation/corpora/crag-gold-v1-draft"))
    corpus_lock.add_argument("--output", type=Path, required=True)
    corpus_lock.set_defaults(handler=_corpus_lock_command)
    corpus_reviews = commands.add_parser(
        "corpus-apply-reviews", help="Apply accountable human review and adjudication records"
    )
    corpus_reviews.add_argument("--corpus", type=Path, default=Path("evaluation/corpora/crag-gold-v1-draft"))
    corpus_reviews.add_argument("--reviews", type=Path, required=True)
    corpus_reviews.add_argument("--adjudications", type=Path)
    corpus_reviews.set_defaults(handler=_corpus_apply_reviews_command)
    corpus_verify = commands.add_parser("corpus-verify-lock", help="Verify a locked corpus checksum set")
    corpus_verify.add_argument("--corpus", type=Path, required=True)
    corpus_verify.set_defaults(handler=_corpus_verify_lock_command)
    return result


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
