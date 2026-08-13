from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class GoldEvidence(BaseModel):
    fixture: str | None = None
    text_contains: str = Field(min_length=1)
    relevance: int = Field(default=1, ge=1, le=3)
    page: int | None = Field(default=None, ge=1)
    paragraph: int | None = Field(default=None, ge=0)


class GoldClaim(BaseModel):
    text: str = Field(min_length=1)
    supported: bool = True


class BenchmarkCase(BaseModel):
    id: str = Field(min_length=1)
    language: Literal["en", "ar", "mixed"]
    category: Literal[
        "answerable",
        "correction_required",
        "unanswerable",
        "partial",
        "contradictory",
        "prompt_injection",
    ]
    question: str = Field(min_length=2)
    fixture: str
    additional_fixtures: list[str] = Field(default_factory=list)
    label_status: Literal["pending_human_anchor", "provisional", "approved"]
    expected_disposition: Literal["answered", "partial", "refused", "conflicting"] | None = None
    gold_evidence: list[GoldEvidence] = Field(default_factory=list)
    gold_claims: list[GoldClaim] = Field(default_factory=list)
    reviewer: str | None = None
    adjudicator: str | None = None
    notes: str | None = None

    @property
    def fixtures(self) -> list[str]:
        return [self.fixture, *self.additional_fixtures]

    def acceptance_errors(self) -> list[str]:
        errors: list[str] = []
        if self.label_status != "approved":
            errors.append("label_status is not approved")
        if not self.reviewer:
            errors.append("reviewer is missing")
        if self.expected_disposition is None:
            errors.append("expected_disposition is missing")
        if self.category not in {"unanswerable", "prompt_injection"} and not self.gold_evidence:
            errors.append("gold_evidence is missing")
        return errors


@dataclass(frozen=True, slots=True)
class ManifestAudit:
    total_cases: int
    approved_cases: int
    missing_fixtures: tuple[str, ...]
    case_errors: dict[str, list[str]]

    @property
    def acceptance_ready(self) -> bool:
        return (
            self.total_cases > 0
            and self.approved_cases == self.total_cases
            and not self.missing_fixtures
            and not self.case_errors
        )

    def model_dump(self) -> dict[str, object]:
        payload = asdict(self)
        payload["acceptance_ready"] = self.acceptance_ready
        return payload


def load_manifest(path: Path) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(BenchmarkCase.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"Invalid benchmark case at {path}:{line_number}: {exc}") from exc
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Manifest contains duplicate case IDs: {path}")
    return cases


def audit_manifest(cases: list[BenchmarkCase], fixture_dir: Path) -> ManifestAudit:
    missing = sorted(
        {
            fixture
            for case in cases
            for fixture in case.fixtures
            if not (fixture_dir / fixture).is_file()
        }
    )
    errors = {case.id: case.acceptance_errors() for case in cases}
    return ManifestAudit(
        total_cases=len(cases),
        approved_cases=sum(case.label_status == "approved" for case in cases),
        missing_fixtures=tuple(missing),
        case_errors={case_id: values for case_id, values in errors.items() if values},
    )


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    recall_at_k: float
    mean_reciprocal_rank: float
    ndcg_at_k: float


def retrieval_metrics(
    rankings: list[list[str]],
    relevant: list[set[str]],
    k: int,
    graded_relevance: list[dict[str, int]] | None = None,
) -> RetrievalMetrics:
    if len(rankings) != len(relevant):
        raise ValueError("Rankings and relevance labels must contain the same number of queries.")
    if graded_relevance is not None and len(graded_relevance) != len(rankings):
        raise ValueError("Graded relevance labels must contain the same number of queries.")
    if not rankings:
        return RetrievalMetrics(0.0, 0.0, 0.0)
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    for query_index, (ranked, expected) in enumerate(zip(rankings, relevant, strict=True)):
        top = ranked[:k]
        recalls.append(len(set(top) & expected) / max(len(expected), 1))
        first = next((index for index, item in enumerate(ranked, start=1) if item in expected), None)
        reciprocal_ranks.append(1 / first if first else 0.0)
        grades = graded_relevance[query_index] if graded_relevance else {item: 1 for item in expected}
        dcg = sum(
            ((2 ** grades.get(item, 0) - 1) / math.log2(index + 2))
            for index, item in enumerate(top)
        )
        ideal_grades = sorted(grades.values(), reverse=True)[:k]
        ideal = sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(ideal_grades))
        ndcgs.append(dcg / ideal if ideal else 0.0)
    size = len(rankings)
    return RetrievalMetrics(
        recall_at_k=sum(recalls) / size,
        mean_reciprocal_rank=sum(reciprocal_ranks) / size,
        ndcg_at_k=sum(ndcgs) / size,
    )


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    precision: float
    recall: float
    f1: float
    false_supported: int
    false_supported_rate: float
    true_supported: int
    true_unsupported: int
    false_unsupported: int


def support_metrics(predicted_supported: list[bool], actual_supported: list[bool]) -> ClassificationMetrics:
    if len(predicted_supported) != len(actual_supported):
        raise ValueError("Predictions and labels must contain the same number of cases.")
    true_positive = sum(p and a for p, a in zip(predicted_supported, actual_supported, strict=True))
    false_positive = sum(p and not a for p, a in zip(predicted_supported, actual_supported, strict=True))
    false_negative = sum(not p and a for p, a in zip(predicted_supported, actual_supported, strict=True))
    true_negative = sum(not p and not a for p, a in zip(predicted_supported, actual_supported, strict=True))
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    unsupported = false_positive + true_negative
    return ClassificationMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        false_supported=false_positive,
        false_supported_rate=false_positive / max(unsupported, 1),
        true_supported=true_positive,
        true_unsupported=true_negative,
        false_unsupported=false_negative,
    )


@dataclass(frozen=True, slots=True)
class CorrectionMetrics:
    improved: int
    unchanged: int
    regressed: int
    pre_retrieval: RetrievalMetrics
    post_retrieval: RetrievalMetrics


def correction_metrics(
    pre_rankings: list[list[str]],
    post_rankings: list[list[str]],
    relevant: list[set[str]],
    k: int,
) -> CorrectionMetrics:
    if not (len(pre_rankings) == len(post_rankings) == len(relevant)):
        raise ValueError("Correction rankings and labels must contain the same number of queries.")

    def first_rank(ranking: list[str], expected: set[str]) -> int:
        return next((index for index, value in enumerate(ranking, start=1) if value in expected), len(ranking) + 1)

    improved = unchanged = regressed = 0
    for before, after, expected in zip(pre_rankings, post_rankings, relevant, strict=True):
        before_key = (len(set(before[:k]) & expected), -first_rank(before, expected))
        after_key = (len(set(after[:k]) & expected), -first_rank(after, expected))
        if after_key > before_key:
            improved += 1
        elif after_key < before_key:
            regressed += 1
        else:
            unchanged += 1
    return CorrectionMetrics(
        improved=improved,
        unchanged=unchanged,
        regressed=regressed,
        pre_retrieval=retrieval_metrics(pre_rankings, relevant, k),
        post_retrieval=retrieval_metrics(post_rankings, relevant, k),
    )
