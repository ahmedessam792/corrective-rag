from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from crag.ingestion import chunk_blocks, parse_document

SCHEMA_VERSION = "1.0"
EXPECTED_CASES = 60
EXPECTED_LANGUAGE_COUNTS = {"en": 30, "ar": 30}
EXPECTED_CATEGORY_COUNTS = {
    "answerable": 10,
    "correction_required": 10,
    "unanswerable": 10,
    "partial": 10,
    "contradictory": 10,
    "prompt_injection": 10,
}
EXPECTED_CASE_IDS = {
    f"{language}-{prefix}-{index:02d}"
    for language in ("en", "ar")
    for prefix in ("answerable", "correction", "unanswerable", "partial", "conflict", "injection")
    for index in range(1, 6)
}
OUTCOME_BY_CATEGORY = {
    "answerable": "SUPPORTED",
    "correction_required": "SUPPORTED",
    "unanswerable": "INSUFFICIENT",
    "partial": "PARTIAL",
    "contradictory": "CONTRADICTORY",
    "prompt_injection": "SUPPORTED",
}
MANDATORY_ADJUDICATION_CATEGORIES = {
    "unanswerable",
    "partial",
    "contradictory",
    "prompt_injection",
}
REVIEW_BATCH_CATEGORY_ORDER = (
    "answerable",
    "correction_required",
    "unanswerable",
    "partial",
    "contradictory",
    "prompt_injection",
)
RUNTIME_ALLOWED_KEYS = {"id", "question", "sources"}
RUNTIME_PROHIBITED_KEYS = {
    "category",
    "expected_outcome",
    "gold_evidence",
    "gold_claims",
    "correction",
    "human_review_state",
    "reviewer_id",
    "review_record_id",
    "adjudication_record_id",
    "uncertainty",
    "notes",
}


class Outcome(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    CONTRADICTORY = "CONTRADICTORY"


class EvidenceRole(StrEnum):
    NECESSARY = "necessary"
    ACCEPTABLE_ALTERNATIVE = "acceptable_alternative"
    BRIDGE = "bridge"
    CONFLICTING = "conflicting"


class ClaimExpectation(StrEnum):
    SUPPORTED = "supported"
    ABSENT = "absent"
    CONFLICTED = "conflicted"


class ReviewState(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    ADJUDICATION_REQUIRED = "adjudication_required"
    ADJUDICATED = "adjudicated"
    APPROVED = "approved"
    LOCKED = "locked"


class CorpusStatus(StrEnum):
    DRAFT = "draft"
    LOCKED = "locked"


class SourceLocator(BaseModel):
    page: int | None = Field(default=None, ge=1)
    heading_path: list[str] = Field(default_factory=list)
    paragraph_start: int | None = Field(default=None, ge=0)
    paragraph_end: int | None = Field(default=None, ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_range(self) -> SourceLocator:
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if self.paragraph_start is not None and self.paragraph_end is None:
            self.paragraph_end = self.paragraph_start
        if (
            self.paragraph_start is not None
            and self.paragraph_end is not None
            and self.paragraph_end < self.paragraph_start
        ):
            raise ValueError("paragraph_end must not precede paragraph_start")
        return self


class EvidenceAnchor(BaseModel):
    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    role: EvidenceRole
    exact_text: str = Field(min_length=1)
    normalized_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relevance: int = Field(ge=1, le=3)
    locator: SourceLocator
    claim_ids: list[str] = Field(min_length=1)
    alternative_group: str | None = None

    @model_validator(mode="after")
    def validate_alternative(self) -> EvidenceAnchor:
        if self.role == EvidenceRole.ACCEPTABLE_ALTERNATIVE and not self.alternative_group:
            raise ValueError("acceptable alternative evidence requires alternative_group")
        return self


class GoldClaim(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    expectation: ClaimExpectation


class CorrectionGold(BaseModel):
    required: bool
    rationale: str | None = None
    bridge_anchor_ids: list[str] = Field(default_factory=list)
    target_anchor_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_required(self) -> CorrectionGold:
        if self.required and (not self.rationale or not self.bridge_anchor_ids or not self.target_anchor_ids):
            raise ValueError("required correction needs rationale plus bridge and target anchors")
        if not self.required and (self.bridge_anchor_ids or self.target_anchor_ids):
            raise ValueError("non-correction cases cannot carry correction anchor IDs")
        return self


class CaseProvenance(BaseModel):
    case_revision: int = Field(default=1, ge=1)
    authoring_method: str = Field(min_length=1)
    assistance: str = Field(min_length=1)
    source_spec_version: str = Field(min_length=1)


class GoldCase(BaseModel):
    id: str = Field(min_length=1)
    language: Literal["en", "ar"]
    category: Literal[
        "answerable",
        "correction_required",
        "unanswerable",
        "partial",
        "contradictory",
        "prompt_injection",
    ]
    question: str = Field(min_length=2)
    source_ids: list[str] = Field(min_length=1)
    expected_outcome: Outcome
    gold_evidence: list[EvidenceAnchor] = Field(default_factory=list)
    gold_claims: list[GoldClaim] = Field(min_length=1)
    absence_scope: Literal["all_case_sources"] | None = None
    missing_information: str | None = None
    correction: CorrectionGold
    citation_sensitive: bool = True
    human_review_state: ReviewState = ReviewState.DRAFT
    reviewer_id: str | None = None
    review_record_id: str | None = None
    adjudication_record_id: str | None = None
    uncertainty: list[str] = Field(default_factory=list)
    provenance: CaseProvenance


class SourceRecord(BaseModel):
    source_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    logical_fixture: str = Field(min_length=1)
    language: Literal["en", "ar"]
    media_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    title: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance: str = Field(min_length=1)
    rights: str = Field(min_length=1)


class ReviewRecord(BaseModel):
    review_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    reviewer_role: Literal["bilingual_primary"]
    reviewed_outcome: Outcome
    approved_anchor_ids: list[str]
    reviewed_correction_required: bool
    confidence: Literal["high", "medium", "low"]
    uncertainty: list[str] = Field(default_factory=list)
    decision: Literal["approved", "changes_required", "adjudication_required"]
    notes: str = Field(min_length=1)
    reviewed_at: str = Field(min_length=1)

    @field_validator("reviewed_at")
    @classmethod
    def validate_reviewed_at(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("reviewed_at must include a timezone")
        return value


class AdjudicationRecord(BaseModel):
    adjudication_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    review_id: str = Field(min_length=1)
    adjudicator_id: str = Field(min_length=1)
    adjudicator_role: Literal["safety_adjudicator"]
    original_outcome: Outcome
    dispute_reason: str = Field(min_length=1)
    adjudicated_outcome: Outcome
    approved_anchor_ids: list[str]
    adjudicated_correction_required: bool
    decision: Literal["approved", "changes_required"]
    notes: str = Field(min_length=1)
    adjudicated_at: str = Field(min_length=1)

    @field_validator("adjudicated_at")
    @classmethod
    def validate_adjudicated_at(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("adjudicated_at must include a timezone")
        return value


class CorpusMetadata(BaseModel):
    corpus_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    schema_version: str = SCHEMA_VERSION
    status: CorpusStatus
    created_at: str = Field(min_length=1)
    description: str = Field(min_length=1)
    case_manifest: str = "gold_cases.jsonl"
    source_manifest: str = "sources.jsonl"
    runtime_manifest: str = "runtime_cases.jsonl"
    review_manifest: str = "reviews.jsonl"
    adjudication_manifest: str = "adjudications.jsonl"
    fixture_root: str = "fixtures"
    parent_version: str | None = None
    aggregate_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class CorpusAudit:
    corpus_id: str
    version: str
    status: str
    total_cases: int
    structurally_complete_cases: int
    approved_cases: int
    missing_sources: tuple[str, ...]
    unresolved_reviews: tuple[str, ...]
    unresolved_adjudications: tuple[str, ...]
    integrity_errors: tuple[str, ...]
    case_errors: dict[str, list[str]]

    @property
    def benchmark_ready(self) -> bool:
        return (
            self.status == CorpusStatus.LOCKED
            and self.total_cases == EXPECTED_CASES
            and self.approved_cases == EXPECTED_CASES
            and not self.missing_sources
            and not self.unresolved_reviews
            and not self.unresolved_adjudications
            and not self.integrity_errors
            and not self.case_errors
        )

    @property
    def verdict(self) -> str:
        if self.benchmark_ready:
            return "Gold corpus locked and benchmark-ready"
        if self.missing_sources:
            return "Corpus blocked by fixture/source issues"
        if self.total_cases == EXPECTED_CASES and self.structurally_complete_cases == EXPECTED_CASES:
            return "Corpus complete but human approval pending"
        return "Corpus incomplete"

    def model_dump(self) -> dict[str, Any]:
        result = asdict(self)
        result["benchmark_ready"] = self.benchmark_ready
        result["verdict"] = self.verdict
        return result


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def normalize_extracted_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    arabic_compatibility = str.maketrans({"ی": "ي", "ى": "ي", "ھ": "ه", "ک": "ك"})
    return " ".join(normalized.translate(arabic_compatibility).split())


def text_sha256(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: Path, model: type[BaseModel]) -> list[Any]:
    if not path.is_file():
        return []
    result = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            result.append(model.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"Invalid record at {path}:{line_number}: {exc}") from exc
    return result


def _write_jsonl(path: Path, records: list[BaseModel]) -> None:
    path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )


def load_corpus(
    root: Path,
) -> tuple[
    CorpusMetadata,
    list[GoldCase],
    list[SourceRecord],
    list[ReviewRecord],
    list[AdjudicationRecord],
]:
    metadata = CorpusMetadata.model_validate_json((root / "corpus.json").read_text(encoding="utf-8"))
    return (
        metadata,
        _load_jsonl(root / metadata.case_manifest, GoldCase),
        _load_jsonl(root / metadata.source_manifest, SourceRecord),
        _load_jsonl(root / metadata.review_manifest, ReviewRecord),
        _load_jsonl(root / metadata.adjudication_manifest, AdjudicationRecord),
    )


def _anchor_error(root: Path, source: SourceRecord, anchor: EvidenceAnchor) -> str | None:
    path = root / source.relative_path
    if not path.is_file():
        return "source file is missing"
    blocks = parse_document(path, source.media_type, ocr_requested=False)
    candidates = []
    for block in blocks:
        if anchor.locator.page is not None and block.anchor.page != anchor.locator.page:
            continue
        if anchor.locator.paragraph_start is not None:
            start = block.anchor.paragraph_start
            end = block.anchor.paragraph_end if block.anchor.paragraph_end is not None else start
            if start is None or end is None or not start <= anchor.locator.paragraph_start <= end:
                continue
        normalized_block = normalize_extracted_text(block.text)
        normalized_anchor = normalize_extracted_text(anchor.exact_text)
        offset = normalized_block.find(normalized_anchor)
        if offset >= 0:
            candidates.append((block, offset, offset + len(normalized_anchor)))
    if len(candidates) != 1:
        return f"anchor {anchor.id} resolved {len(candidates)} times; expected exactly one"
    block, start, end = candidates[0]
    if (start, end) != (anchor.locator.char_start, anchor.locator.char_end):
        return f"anchor {anchor.id} character range does not match extracted normalized text"
    if text_sha256(anchor.exact_text) != anchor.normalized_text_sha256:
        return f"anchor {anchor.id} passage hash is invalid"
    if anchor.locator.heading_path and block.anchor.heading_path != anchor.locator.heading_path:
        return f"anchor {anchor.id} heading path does not match"
    return None


def _case_errors(case: GoldCase, source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if case.expected_outcome.value != OUTCOME_BY_CATEGORY[case.category]:
        errors.append("expected_outcome does not match the frozen category matrix")
    if case.correction.required != (case.category == "correction_required"):
        errors.append("correction.required does not match the frozen category matrix")
    unknown_sources = set(case.source_ids) - source_ids
    if unknown_sources:
        errors.append(f"unknown source IDs: {', '.join(sorted(unknown_sources))}")
    claim_ids = {claim.id for claim in case.gold_claims}
    if len(claim_ids) != len(case.gold_claims):
        errors.append("claim IDs are not unique within the case")
    anchor_ids = {anchor.id for anchor in case.gold_evidence}
    if len(anchor_ids) != len(case.gold_evidence):
        errors.append("anchor IDs are not unique within the case")
    for anchor in case.gold_evidence:
        if anchor.source_id not in case.source_ids:
            errors.append(f"anchor {anchor.id} references a source outside the case")
        if set(anchor.claim_ids) - claim_ids:
            errors.append(f"anchor {anchor.id} references an unknown claim")
    if case.category == "unanswerable":
        if case.gold_evidence:
            errors.append("unanswerable case must not contain positive gold evidence")
        if case.absence_scope != "all_case_sources" or not case.missing_information:
            errors.append("unanswerable case requires a reviewed all-source absence assertion")
    elif not case.gold_evidence:
        errors.append("case requires gold evidence")
    if case.category == "partial":
        expectations = {claim.expectation for claim in case.gold_claims}
        if not {ClaimExpectation.SUPPORTED, ClaimExpectation.ABSENT} <= expectations:
            errors.append("partial case requires supported and absent atomic claims")
    if case.category == "contradictory":
        if len(case.source_ids) < 2:
            errors.append("contradictory case requires at least two sources")
        conflicting_sources = {
            anchor.source_id for anchor in case.gold_evidence if anchor.role == EvidenceRole.CONFLICTING
        }
        if len(conflicting_sources) < 2:
            errors.append("contradictory case requires conflicting anchors from two sources")
    if case.correction.required:
        if set(case.correction.bridge_anchor_ids) - anchor_ids:
            errors.append("correction bridge anchor is missing")
        if set(case.correction.target_anchor_ids) - anchor_ids:
            errors.append("correction target anchor is missing")
    return errors


def _validate_runtime_manifest(
    root: Path, metadata: CorpusMetadata, source_by_id: dict[str, SourceRecord]
) -> list[str]:
    path = root / metadata.runtime_manifest
    if not path.is_file():
        return ["runtime manifest is missing"]
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        keys = set(payload)
        if keys != RUNTIME_ALLOWED_KEYS:
            errors.append(f"runtime line {line_number} has disallowed or missing keys: {sorted(keys)}")
        if keys & RUNTIME_PROHIBITED_KEYS:
            errors.append(f"runtime line {line_number} leaks evaluator-only keys")
        for source in payload.get("sources", []):
            if set(source) != {"source_id", "relative_path", "sha256"}:
                errors.append(f"runtime line {line_number} contains disallowed source metadata")
            if source.get("source_id") not in source_by_id:
                errors.append(f"runtime line {line_number} references an unknown source")
    return errors


def audit_corpus(root: Path, *, verify_lock: bool = True, verify_documents: bool = True) -> CorpusAudit:
    metadata, cases, sources, reviews, adjudications = load_corpus(root)
    integrity_errors: list[str] = []
    missing_sources: list[str] = []
    case_errors: dict[str, list[str]] = {}
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        integrity_errors.append("case IDs are not unique")
    if set(ids) != EXPECTED_CASE_IDS:
        integrity_errors.append("case IDs do not match the frozen 60-case definition")
    normalized_questions = [(case.language, normalize_text(case.question).casefold()) for case in cases]
    if len(normalized_questions) != len(set(normalized_questions)):
        integrity_errors.append("duplicate normalized questions exist within a language")
    source_ids = [source.source_id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        integrity_errors.append("source IDs are not unique")
    language_counts = Counter(case.language for case in cases)
    category_counts = Counter(case.category for case in cases)
    if len(cases) != EXPECTED_CASES:
        integrity_errors.append(f"expected {EXPECTED_CASES} cases, found {len(cases)}")
    if dict(language_counts) != EXPECTED_LANGUAGE_COUNTS:
        integrity_errors.append(f"language distribution is {dict(language_counts)}")
    if dict(category_counts) != EXPECTED_CATEGORY_COUNTS:
        integrity_errors.append(f"category distribution is {dict(category_counts)}")
    source_by_id = {source.source_id: source for source in sources}
    seen_hashes: dict[str, str] = {}
    for source in sources:
        path = root / source.relative_path
        if not path.is_file():
            missing_sources.append(source.source_id)
            continue
        digest = file_sha256(path)
        if digest != source.sha256:
            integrity_errors.append(f"source hash mismatch: {source.source_id}")
        if verify_documents:
            try:
                blocks = parse_document(path, source.media_type, ocr_requested=False)
                if not blocks:
                    integrity_errors.append(f"source has no accessible extracted text: {source.source_id}")
            except Exception as exc:
                integrity_errors.append(f"source is inaccessible: {source.source_id}: {type(exc).__name__}")
        prior = seen_hashes.get(digest)
        if prior and prior != source.source_id:
            integrity_errors.append(f"undeclared duplicate source bytes: {prior}, {source.source_id}")
        seen_hashes[digest] = source.source_id
    fixture_root = root / metadata.fixture_root
    registered_fixture_paths = {(root / source.relative_path).resolve() for source in sources}
    actual_fixture_paths = (
        {path.resolve() for path in fixture_root.rglob("*") if path.is_file()} if fixture_root.is_dir() else set()
    )
    unregistered = sorted(path.relative_to(root).as_posix() for path in actual_fixture_paths - registered_fixture_paths)
    if unregistered:
        integrity_errors.append(f"unregistered fixture files: {unregistered}")
    for case in cases:
        errors = _case_errors(case, set(source_ids))
        if verify_documents:
            for anchor in case.gold_evidence:
                source = source_by_id.get(anchor.source_id)
                if source:
                    error = _anchor_error(root, source, anchor)
                    if error:
                        errors.append(error)
        if verify_documents and case.correction.required and not errors:
            case_chunks = []
            for source_id in case.source_ids:
                source = source_by_id[source_id]
                blocks = parse_document(root / source.relative_path, source.media_type, ocr_requested=False)
                case_chunks.extend(
                    chunk_blocks(
                        blocks,
                        document_id=source_id,
                        workspace_id="corpus-audit",
                        filename=Path(source.relative_path).name,
                    )
                )
            if len(case_chunks) < 13:
                errors.append("correction case requires at least 13 structurally distinct candidate chunks")
            anchor_by_id = {anchor.id: anchor for anchor in case.gold_evidence}
            bridge_texts = [
                normalize_extracted_text(anchor_by_id[anchor_id].exact_text)
                for anchor_id in case.correction.bridge_anchor_ids
            ]
            target_texts = [
                normalize_extracted_text(anchor_by_id[anchor_id].exact_text)
                for anchor_id in case.correction.target_anchor_ids
            ]
            bridge_chunks = {
                index
                for index, chunk in enumerate(case_chunks)
                if any(text in normalize_extracted_text(chunk.text) for text in bridge_texts)
            }
            target_chunks = {
                index
                for index, chunk in enumerate(case_chunks)
                if any(text in normalize_extracted_text(chunk.text) for text in target_texts)
            }
            if not bridge_chunks or not target_chunks or bridge_chunks & target_chunks:
                errors.append("correction bridge and target must resolve to separate candidate chunks")
        if errors:
            case_errors[case.id] = errors
    review_by_case = {record.case_id: record for record in reviews}
    adjudication_by_case = {record.case_id: record for record in adjudications}
    unresolved_reviews: list[str] = []
    unresolved_adjudications: list[str] = []
    approved_cases = 0
    for case in cases:
        mandatory = case.category in MANDATORY_ADJUDICATION_CATEGORIES
        review = review_by_case.get(case.id)
        if not review or review.decision not in {"approved", "adjudication_required"}:
            unresolved_reviews.append(case.id)
            if mandatory:
                unresolved_adjudications.append(case.id)
            continue
        if (
            review.reviewed_outcome != case.expected_outcome
            or review.reviewed_correction_required != case.correction.required
            or set(review.approved_anchor_ids) != {anchor.id for anchor in case.gold_evidence}
        ):
            case_errors.setdefault(case.id, []).append("primary review does not match current gold data")
            continue
        needs_adjudication = mandatory or review.decision == "adjudication_required" or review.confidence != "high"
        if needs_adjudication:
            adjudication = adjudication_by_case.get(case.id)
            if not adjudication or adjudication.decision != "approved":
                unresolved_adjudications.append(case.id)
                continue
            if (
                adjudication.review_id != review.review_id
                or adjudication.original_outcome != review.reviewed_outcome
                or adjudication.adjudicated_outcome != case.expected_outcome
                or adjudication.adjudicated_correction_required != case.correction.required
                or set(adjudication.approved_anchor_ids) != {anchor.id for anchor in case.gold_evidence}
                or adjudication.adjudicator_id == review.reviewer_id
            ):
                case_errors.setdefault(case.id, []).append(
                    "adjudication does not approve the current independent gold data"
                )
                continue
        if case.human_review_state in {ReviewState.APPROVED, ReviewState.LOCKED}:
            approved_cases += 1
        else:
            case_errors.setdefault(case.id, []).append("human_review_state is not approved or locked")
    integrity_errors.extend(_validate_runtime_manifest(root, metadata, source_by_id))
    if metadata.status == CorpusStatus.LOCKED and verify_lock:
        integrity_errors.extend(verify_locked_corpus(root))
    structurally_complete = sum(
        case.id not in case_errors
        or all(error == "human_review_state is not approved or locked" for error in case_errors[case.id])
        for case in cases
    )
    return CorpusAudit(
        corpus_id=metadata.corpus_id,
        version=metadata.version,
        status=metadata.status,
        total_cases=len(cases),
        structurally_complete_cases=structurally_complete,
        approved_cases=approved_cases,
        missing_sources=tuple(sorted(missing_sources)),
        unresolved_reviews=tuple(sorted(unresolved_reviews)),
        unresolved_adjudications=tuple(sorted(unresolved_adjudications)),
        integrity_errors=tuple(sorted(set(integrity_errors))),
        case_errors=case_errors,
    )


def compile_runtime_manifest(root: Path) -> Path:
    metadata, cases, sources, _, _ = load_corpus(root)
    source_by_id = {source.source_id: source for source in sources}
    records = []
    for case in cases:
        records.append(
            {
                "id": case.id,
                "question": unicodedata.normalize("NFC", case.question),
                "sources": [
                    {
                        "source_id": source_id,
                        "relative_path": source_by_id[source_id].relative_path,
                        "sha256": source_by_id[source_id].sha256,
                    }
                    for source_id in case.source_ids
                ],
            }
        )
    path = root / metadata.runtime_manifest
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )
    return path


def _review_case_payload(case: GoldCase, source_by_id: dict[str, SourceRecord]) -> dict[str, Any]:
    return {
        "case_id": case.id,
        "language": case.language,
        "category": case.category,
        "question": case.question,
        "proposal": {
            "expected_outcome": case.expected_outcome,
            "correction_required": case.correction.required,
            "correction_rationale": case.correction.rationale,
            "correction_bridge_anchor_ids": case.correction.bridge_anchor_ids,
            "correction_target_anchor_ids": case.correction.target_anchor_ids,
            "absence_scope": case.absence_scope,
            "missing_information": case.missing_information,
            "claims": [claim.model_dump(mode="json") for claim in case.gold_claims],
            "evidence": [anchor.model_dump(mode="json") for anchor in case.gold_evidence],
        },
        "sources": [
            {
                "source_id": source.source_id,
                "title": source.title,
                "relative_path": source.relative_path,
                "document_version": source.document_version,
                "sha256": source.sha256,
            }
            for source_id in case.source_ids
            for source in [source_by_id[source_id]]
        ],
    }


def _markdown_locator(anchor: EvidenceAnchor) -> str:
    locator = anchor.locator
    parts = []
    if locator.page is not None:
        parts.append(f"page {locator.page}")
    if locator.heading_path:
        parts.append("heading " + " / ".join(locator.heading_path))
    if locator.paragraph_start is not None:
        paragraph = str(locator.paragraph_start)
        if locator.paragraph_end != locator.paragraph_start:
            paragraph += f"-{locator.paragraph_end}"
        parts.append(f"paragraph {paragraph}")
    parts.append(f"characters {locator.char_start}-{locator.char_end}")
    return ", ".join(parts)


def _primary_markdown(
    *,
    corpus_id: str,
    version: str,
    batch_id: str,
    cases: list[GoldCase],
    source_by_id: dict[str, SourceRecord],
    heading: str = "Primary review batch",
    include_primary_response: bool = True,
) -> str:
    lines = [
        f"# {heading}: {batch_id}",
        "",
        f"Corpus: `{corpus_id}` / `{version}`",
        "",
        "This packet contains evaluator-only proposals. Inspect every source directly before deciding. "
        "Do not treat the proposal or any model assistance as approved truth.",
        "",
    ]
    for case in cases:
        lines.extend(
            [
                f"## {case.id}",
                "",
                f"- Language: `{case.language}`",
                f"- Question: {case.question}",
                f"- Proposed outcome: `{case.expected_outcome}`",
                f"- Proposed correction required: `{str(case.correction.required).lower()}`",
            ]
        )
        if case.correction.rationale:
            lines.append(f"- Correction rationale: {case.correction.rationale}")
        if case.absence_scope:
            lines.append(f"- Absence scope: `{case.absence_scope}`")
        if case.missing_information:
            lines.append(f"- Missing information: {case.missing_information}")
        lines.extend(["", "Sources:", ""])
        for source_id in case.source_ids:
            source = source_by_id[source_id]
            lines.append(
                f"- `{source.source_id}` — {source.title}; `{source.relative_path}`; "
                f"version `{source.document_version}`; SHA-256 `{source.sha256}`"
            )
        lines.extend(["", "Proposed atomic claims:", ""])
        for claim in case.gold_claims:
            lines.append(f"- `{claim.id}` (`{claim.expectation}`): {claim.text}")
        lines.extend(["", "Proposed evidence anchors:", ""])
        if not case.gold_evidence:
            lines.append("- None. Confirm the stated missing information is absent from every listed source.")
        for anchor in case.gold_evidence:
            lines.extend(
                [
                    f"- `{anchor.id}` — source `{anchor.source_id}`, role `{anchor.role}`, "
                    f"{_markdown_locator(anchor)}",
                    f"  - Exact passage: “{anchor.exact_text}”",
                    f"  - Passage SHA-256: `{anchor.normalized_text_sha256}`",
                    f"  - Claims: {', '.join(f'`{claim_id}`' for claim_id in anchor.claim_ids)}",
                ]
            )
        if include_primary_response:
            lines.extend(
                [
                    "",
                    "Reviewer decision (complete the companion JSONL record):",
                    "",
                    "- Decision: `approved` / `changes_required` / `adjudication_required`",
                    "- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`",
                    "- Reviewed correction required: `true` / `false`",
                    "- Approved anchor IDs:",
                    "- Confidence: `high` / `medium` / `low`",
                    "- Uncertainty:",
                    "- Notes:",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _adjudication_markdown(
    *,
    corpus_id: str,
    version: str,
    batch_id: str,
    cases: list[GoldCase],
    source_by_id: dict[str, SourceRecord],
    review_by_case: dict[str, ReviewRecord],
) -> str:
    primary = _primary_markdown(
        corpus_id=corpus_id,
        version=version,
        batch_id=batch_id,
        cases=cases,
        source_by_id=source_by_id,
        heading="Adjudication evidence batch",
        include_primary_response=False,
    )
    lines = [
        primary.rstrip(),
        "",
        "# Preserved primary decisions",
        "",
        "The adjudicator must independently inspect the sources. The records below preserve, but do not "
        "replace, that independent judgment.",
        "",
    ]
    for case in cases:
        review = review_by_case[case.id]
        lines.extend(
            [
                f"## {case.id} primary record",
                "",
                f"- Review ID: `{review.review_id}`",
                f"- Primary reviewer: `{review.reviewer_id}`",
                f"- Decision: `{review.decision}`",
                f"- Reviewed outcome: `{review.reviewed_outcome}`",
                f"- Reviewed correction required: `{str(review.reviewed_correction_required).lower()}`",
                f"- Approved anchor IDs: {', '.join(f'`{anchor_id}`' for anchor_id in review.approved_anchor_ids)}",
                f"- Confidence: `{review.confidence}`",
                f"- Uncertainty: {'; '.join(review.uncertainty) if review.uncertainty else 'None recorded'}",
                f"- Notes: {review.notes}",
                "",
                "Adjudicator response (complete the companion JSONL record):",
                "",
                "- Dispute or mandatory-safety reason:",
                "- Adjudicated outcome:",
                "- Approved anchor IDs:",
                "- Adjudicated correction required:",
                "- Decision: `approved` / `changes_required`",
                "- Notes:",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _write_review_artifact(path: Path, content: str) -> None:
    if path.exists():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise FileExistsError(
                f"Review artifact already exists with different content; preserve it and choose a new output: {path}"
            )
        return
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_packet(path: Path, payload: dict[str, Any]) -> None:
    _write_review_artifact(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _prepare_batch_directory(output: Path) -> None:
    if output.exists():
        if not output.is_dir():
            raise ValueError(f"Review batch output is not a directory: {output}")
    else:
        output.mkdir(parents=True)


def prepare_primary_review_batches(
    root: Path,
    output: Path | None = None,
    *,
    verify_documents: bool = True,
) -> Path:
    """Create evaluator-only bilingual review packets without changing corpus state."""
    audit = audit_corpus(root, verify_lock=False, verify_documents=verify_documents)
    if audit.missing_sources or audit.integrity_errors or audit.case_errors:
        raise RuntimeError("Primary review packets require a structurally clean corpus audit.")
    metadata, cases, sources, _, _ = load_corpus(root)
    if metadata.status != CorpusStatus.DRAFT:
        raise RuntimeError("Primary review packets may only be prepared from a draft corpus.")
    output = output or root / "review-batches" / "primary"
    _prepare_batch_directory(output)
    source_by_id = {source.source_id: source for source in sources}
    manifest_hash = file_sha256(root / metadata.case_manifest)
    source_manifest_hash = file_sha256(root / metadata.source_manifest)
    index: dict[str, Any] = {
        "packet_schema_version": "1.0",
        "stage": "primary",
        "corpus_id": metadata.corpus_id,
        "corpus_version": metadata.version,
        "gold_manifest_sha256": manifest_hash,
        "source_manifest_sha256": source_manifest_hash,
        "case_count": len(cases),
        "batches": [],
    }
    for number, category in enumerate(REVIEW_BATCH_CATEGORY_ORDER, start=1):
        batch_cases = sorted(
            (case for case in cases if case.category == category), key=lambda case: (case.language, case.id)
        )
        batch_id = f"primary-{number:02d}-{category.replace('_', '-')}"
        packet = {
            "packet_schema_version": "1.0",
            "stage": "primary",
            "batch_id": batch_id,
            "corpus_id": metadata.corpus_id,
            "corpus_version": metadata.version,
            "gold_manifest_sha256": manifest_hash,
            "source_manifest_sha256": source_manifest_hash,
            "cases": [_review_case_payload(case, source_by_id) for case in batch_cases],
        }
        _write_packet(output / f"{batch_id}.packet.json", packet)
        _write_review_artifact(
            output / f"{batch_id}.md",
            _primary_markdown(
                corpus_id=metadata.corpus_id,
                version=metadata.version,
                batch_id=batch_id,
                cases=batch_cases,
                source_by_id=source_by_id,
            ),
        )
        response_records = [
            {
                "review_id": f"REPLACE-{case.id}",
                "case_id": case.id,
                "reviewer_id": "REPLACE-WITH-STABLE-HUMAN-ID",
                "reviewer_role": "bilingual_primary",
                "reviewed_outcome": "REPLACE",
                "approved_anchor_ids": ["REPLACE-WITH-APPROVED-ANCHOR-IDS"],
                "reviewed_correction_required": "REPLACE-WITH-TRUE-OR-FALSE",
                "confidence": "REPLACE",
                "uncertainty": ["REPLACE or use an empty list after explicit review"],
                "decision": "REPLACE",
                "notes": "REPLACE after inspecting every listed source and anchor.",
                "reviewed_at": "REPLACE-WITH-TIMEZONE-AWARE-ISO-8601",
            }
            for case in batch_cases
        ]
        _write_review_artifact(
            output / f"{batch_id}.reviews.template.jsonl",
            "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in response_records),
        )
        index["batches"].append({"batch_id": batch_id, "case_ids": [case.id for case in batch_cases]})
    _write_packet(output / "index.json", index)
    return output


def prepare_adjudication_review_batches(root: Path, output: Path | None = None) -> Path:
    """Prepare second-review packets only after valid primary records have been applied."""
    metadata, cases, sources, reviews, _ = load_corpus(root)
    if metadata.status != CorpusStatus.DRAFT:
        raise RuntimeError("Adjudication packets may only be prepared from a draft corpus.")
    review_by_case = {review.case_id: review for review in reviews}
    required_cases = [
        case
        for case in cases
        if case.category in MANDATORY_ADJUDICATION_CATEGORIES
        or (case.id in review_by_case and review_by_case[case.id].decision == "adjudication_required")
        or (case.id in review_by_case and review_by_case[case.id].confidence != "high")
    ]
    missing = sorted(case.id for case in required_cases if case.id not in review_by_case)
    unresolved_changes = sorted(
        case.id
        for case in required_cases
        if review_by_case.get(case.id) and review_by_case[case.id].decision == "changes_required"
    )
    if missing:
        raise RuntimeError("Adjudication packets require completed primary records for: " + ", ".join(missing))
    if unresolved_changes:
        raise RuntimeError(
            "Cases requiring proposal changes must be revised and re-reviewed first: "
            + ", ".join(unresolved_changes)
        )
    output = output or root / "review-batches" / "adjudication"
    _prepare_batch_directory(output)
    source_by_id = {source.source_id: source for source in sources}
    manifest_hash = file_sha256(root / metadata.case_manifest)
    source_manifest_hash = file_sha256(root / metadata.source_manifest)
    review_manifest_hash = file_sha256(root / metadata.review_manifest)
    batches = []
    for number, category in enumerate(REVIEW_BATCH_CATEGORY_ORDER, start=1):
        batch_cases = sorted(
            (case for case in required_cases if case.category == category), key=lambda case: (case.language, case.id)
        )
        if not batch_cases:
            continue
        batch_id = f"adjudication-{number:02d}-{category.replace('_', '-')}"
        packet_cases = []
        response_records = []
        for case in batch_cases:
            review = review_by_case[case.id]
            payload = _review_case_payload(case, source_by_id)
            payload["primary_review"] = review.model_dump(mode="json")
            packet_cases.append(payload)
            response_records.append(
                {
                    "adjudication_id": f"REPLACE-{case.id}",
                    "case_id": case.id,
                    "review_id": review.review_id,
                    "adjudicator_id": "REPLACE-WITH-INDEPENDENT-HUMAN-ID",
                    "adjudicator_role": "safety_adjudicator",
                    "original_outcome": review.reviewed_outcome,
                    "dispute_reason": "REPLACE with the mandatory safety reason or reviewer dispute.",
                    "adjudicated_outcome": "REPLACE",
                    "approved_anchor_ids": ["REPLACE-WITH-APPROVED-ANCHOR-IDS"],
                    "adjudicated_correction_required": "REPLACE-WITH-TRUE-OR-FALSE",
                    "decision": "REPLACE",
                    "notes": "REPLACE after independent source inspection.",
                    "adjudicated_at": "REPLACE-WITH-TIMEZONE-AWARE-ISO-8601",
                }
            )
        _write_packet(
            output / f"{batch_id}.packet.json",
            {
                "packet_schema_version": "1.0",
                "stage": "adjudication",
                "batch_id": batch_id,
                "corpus_id": metadata.corpus_id,
                "corpus_version": metadata.version,
                "gold_manifest_sha256": manifest_hash,
                "source_manifest_sha256": source_manifest_hash,
                "review_manifest_sha256": review_manifest_hash,
                "cases": packet_cases,
            },
        )
        _write_review_artifact(
            output / f"{batch_id}.md",
            _adjudication_markdown(
                corpus_id=metadata.corpus_id,
                version=metadata.version,
                batch_id=batch_id,
                cases=batch_cases,
                source_by_id=source_by_id,
                review_by_case=review_by_case,
            ),
        )
        _write_review_artifact(
            output / f"{batch_id}.adjudications.template.jsonl",
            "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in response_records),
        )
        batches.append({"batch_id": batch_id, "case_ids": [case.id for case in batch_cases]})
    _write_packet(
        output / "index.json",
        {
            "packet_schema_version": "1.0",
            "stage": "adjudication",
            "corpus_id": metadata.corpus_id,
            "corpus_version": metadata.version,
            "gold_manifest_sha256": manifest_hash,
            "source_manifest_sha256": source_manifest_hash,
            "review_manifest_sha256": review_manifest_hash,
            "case_count": len(required_cases),
            "batches": batches,
        },
    )
    return output


def apply_review_records(root: Path, reviews_path: Path, adjudications_path: Path | None = None) -> CorpusAudit:
    metadata, cases, _, _, _ = load_corpus(root)
    if metadata.status == CorpusStatus.LOCKED:
        raise RuntimeError("Locked corpora cannot be edited; create a new corpus version.")
    reviews = _load_jsonl(reviews_path, ReviewRecord)
    adjudications = _load_jsonl(adjudications_path, AdjudicationRecord) if adjudications_path else []
    if len({record.case_id for record in reviews}) != len(reviews):
        raise ValueError("Only one primary review record is allowed per case revision.")
    if len({record.review_id for record in reviews}) != len(reviews):
        raise ValueError("Review record IDs must be unique.")
    if len({record.case_id for record in adjudications}) != len(adjudications):
        raise ValueError("Only one adjudication record is allowed per case revision.")
    if len({record.adjudication_id for record in adjudications}) != len(adjudications):
        raise ValueError("Adjudication record IDs must be unique.")
    prohibited_id_tokens = {"pending", "placeholder", "automatic", "automated", "model", "llm", "ai"}
    for identity in [record.reviewer_id for record in reviews] + [record.adjudicator_id for record in adjudications]:
        identity_tokens = set(re.split(r"[^a-z0-9]+", identity.casefold()))
        if identity_tokens & prohibited_id_tokens:
            raise ValueError("Review identities must identify accountable human roles, not automation or placeholders.")
    review_by_case = {record.case_id: record for record in reviews}
    adjudication_by_case = {record.case_id: record for record in adjudications}
    known_cases = {case.id for case in cases}
    unknown = (set(review_by_case) | set(adjudication_by_case)) - known_cases
    if unknown:
        raise ValueError(f"Review records reference unknown case IDs: {', '.join(sorted(unknown))}")
    case_by_id = {case.id: case for case in cases}
    for review in reviews:
        case = case_by_id[review.case_id]
        if review.decision == "changes_required":
            continue
        if (
            review.reviewed_outcome != case.expected_outcome
            or review.reviewed_correction_required != case.correction.required
            or set(review.approved_anchor_ids) != {anchor.id for anchor in case.gold_evidence}
        ):
            raise ValueError(f"Review does not approve current gold data: {case.id}")
    for adjudication in adjudications:
        case = case_by_id[adjudication.case_id]
        review = review_by_case.get(case.id)
        if not review:
            raise ValueError(f"Adjudication has no matching primary review: {case.id}")
        if adjudication.adjudicator_id == review.reviewer_id:
            raise ValueError(f"Adjudicator must be independent from the primary reviewer: {case.id}")
        if adjudication.review_id != review.review_id or adjudication.original_outcome != review.reviewed_outcome:
            raise ValueError(f"Adjudication does not preserve the original primary decision: {case.id}")
        if adjudication.decision == "approved" and (
            adjudication.adjudicated_outcome != case.expected_outcome
            or adjudication.adjudicated_correction_required != case.correction.required
            or set(adjudication.approved_anchor_ids) != {anchor.id for anchor in case.gold_evidence}
        ):
            raise ValueError(f"Adjudication does not approve current gold data: {case.id}")
    for case in cases:
        review = review_by_case.get(case.id)
        adjudication = adjudication_by_case.get(case.id)
        if not review:
            case.human_review_state = ReviewState.DRAFT
            case.reviewer_id = None
            case.review_record_id = None
            case.adjudication_record_id = None
            continue
        case.reviewer_id = review.reviewer_id
        case.review_record_id = review.review_id
        case.uncertainty = review.uncertainty
        if review.decision == "changes_required":
            case.human_review_state = ReviewState.REVIEWED
            continue
        requires_adjudication = (
            case.category in MANDATORY_ADJUDICATION_CATEGORIES
            or review.decision == "adjudication_required"
            or review.confidence != "high"
        )
        if requires_adjudication and not adjudication:
            case.human_review_state = ReviewState.ADJUDICATION_REQUIRED
            continue
        if adjudication:
            case.adjudication_record_id = adjudication.adjudication_id
            case.human_review_state = (
                ReviewState.APPROVED if adjudication.decision == "approved" else ReviewState.ADJUDICATED
            )
        else:
            case.human_review_state = ReviewState.APPROVED
    _write_jsonl(root / metadata.case_manifest, cases)
    _write_jsonl(root / metadata.review_manifest, reviews)
    _write_jsonl(root / metadata.adjudication_manifest, adjudications)
    return audit_corpus(root, verify_lock=False, verify_documents=False)


def _checksum_entries(root: Path) -> list[tuple[str, str]]:
    excluded = {"checksums.sha256", "integrity-report.json"}
    return [
        (path.relative_to(root).as_posix(), file_sha256(path))
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in excluded
    ]


def _aggregate(entries: list[tuple[str, str]]) -> str:
    payload = "".join(f"{name}\0{digest}\n" for name, digest in entries if name != "corpus.json")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_locked_corpus(root: Path) -> list[str]:
    errors = []
    checksum_path = root / "checksums.sha256"
    if not checksum_path.is_file():
        return ["locked corpus checksums.sha256 is missing"]
    expected: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = dict(_checksum_entries(root))
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
        errors.append(f"lock checksum mismatch; missing={missing}, extra={extra}, changed={changed}")
    metadata = CorpusMetadata.model_validate_json((root / "corpus.json").read_text(encoding="utf-8"))
    if metadata.aggregate_sha256 != _aggregate(list(expected.items())):
        errors.append("corpus aggregate checksum does not match metadata")
    return errors


def lock_corpus(draft_root: Path, locked_root: Path) -> Path:
    if locked_root.exists():
        raise FileExistsError(f"Locked corpus target already exists: {locked_root}")
    audit = audit_corpus(draft_root, verify_lock=False, verify_documents=True)
    prelock_case_errors = {
        case_id: [error for error in errors if error != "human_review_state is not approved or locked"]
        for case_id, errors in audit.case_errors.items()
    }
    prelock_case_errors = {case_id: errors for case_id, errors in prelock_case_errors.items() if errors}
    if (
        audit.total_cases != EXPECTED_CASES
        or audit.structurally_complete_cases != EXPECTED_CASES
        or audit.missing_sources
        or audit.integrity_errors
        or prelock_case_errors
    ):
        raise RuntimeError(f"Corpus is not structurally complete: {json.dumps(audit.model_dump(), ensure_ascii=False)}")
    if audit.approved_cases != EXPECTED_CASES or audit.unresolved_reviews or audit.unresolved_adjudications:
        raise RuntimeError("Lock refused: all 60 cases require explicit human approval and required adjudication.")
    shutil.copytree(draft_root, locked_root)
    metadata, cases, _, _, _ = load_corpus(locked_root)
    metadata.status = CorpusStatus.LOCKED
    metadata.version = locked_root.name
    for case in cases:
        case.human_review_state = ReviewState.LOCKED
    _write_jsonl(locked_root / metadata.case_manifest, cases)
    for auxiliary in (
        "reviews.template.jsonl",
        "adjudications.template.jsonl",
        "review_queue.jsonl",
        "source_specs.jsonl",
    ):
        (locked_root / auxiliary).unlink(missing_ok=True)
    shutil.rmtree(locked_root / "review-batches", ignore_errors=True)
    metadata.aggregate_sha256 = None
    (locked_root / "corpus.json").write_text(
        metadata.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8", newline="\n"
    )
    entries = _checksum_entries(locked_root)
    metadata.aggregate_sha256 = _aggregate(entries)
    (locked_root / "corpus.json").write_text(
        metadata.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8", newline="\n"
    )
    entries = _checksum_entries(locked_root)
    (locked_root / "checksums.sha256").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in entries), encoding="utf-8", newline="\n"
    )
    failures = verify_locked_corpus(locked_root)
    if failures:
        raise RuntimeError(f"Lock verification failed: {failures}")
    report = audit_corpus(locked_root, verify_lock=True, verify_documents=True).model_dump()
    if not report["benchmark_ready"]:
        raise RuntimeError(f"Locked corpus failed final readiness audit: {json.dumps(report, ensure_ascii=False)}")
    report["checksum_verification"] = {"valid": True, "errors": []}
    (locked_root / "integrity-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return locked_root


def now_utc() -> str:
    return datetime.now(UTC).isoformat()
