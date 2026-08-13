from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from crag.corpus import (
    EXPECTED_CASES,
    MANDATORY_ADJUDICATION_CATEGORIES,
    RUNTIME_ALLOWED_KEYS,
    AdjudicationRecord,
    ReviewRecord,
    apply_review_records,
    audit_corpus,
    compile_runtime_manifest,
    load_corpus,
    lock_corpus,
    verify_locked_corpus,
)

CORPUS = Path("evaluation/corpora/crag-gold-v1-draft")


def test_draft_corpus_is_complete_but_not_human_approved() -> None:
    audit = audit_corpus(CORPUS, verify_documents=True)
    assert audit.total_cases == EXPECTED_CASES
    assert audit.structurally_complete_cases == EXPECTED_CASES
    assert audit.approved_cases == 0
    assert not audit.missing_sources
    assert not audit.integrity_errors
    assert not audit.case_errors
    assert len(audit.unresolved_reviews) == EXPECTED_CASES
    assert len(audit.unresolved_adjudications) == 40
    assert audit.verdict == "Corpus complete but human approval pending"
    assert not audit.benchmark_ready


def test_runtime_manifest_contains_only_runtime_inputs() -> None:
    path = compile_runtime_manifest(CORPUS)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == EXPECTED_CASES
    assert all(set(record) == RUNTIME_ALLOWED_KEYS for record in records)
    assert all(
        set(source) == {"source_id", "relative_path", "sha256"} for record in records for source in record["sources"]
    )
    serialized = path.read_text(encoding="utf-8")
    for forbidden in ("expected_outcome", "gold_evidence", "correction_required", "reviewer", "notes"):
        assert forbidden not in serialized


def test_lock_refuses_unapproved_gold(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="explicit human approval"):
        lock_corpus(CORPUS, tmp_path / "crag-gold-v1")


def test_audit_detects_source_tampering(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    source = next((copied / "fixtures").glob("*.docx"))
    source.write_bytes(source.read_bytes() + b"tampered")
    audit = audit_corpus(copied, verify_documents=False)
    assert any("source hash mismatch" in error for error in audit.integrity_errors)


def test_audit_rejects_gold_leakage_in_runtime_manifest(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    runtime = copied / "runtime_cases.jsonl"
    records = [json.loads(line) for line in runtime.read_text(encoding="utf-8").splitlines()]
    records[0]["expected_outcome"] = "SUPPORTED"
    runtime.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    audit = audit_corpus(copied, verify_documents=False)
    assert any("runtime line 1" in error for error in audit.integrity_errors)


def test_arabic_questions_and_evidence_are_nfc() -> None:
    import unicodedata

    for line in (CORPUS / "gold_cases.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["language"] != "ar":
            continue
        assert unicodedata.is_normalized("NFC", record["question"])
        assert all(unicodedata.is_normalized("NFC", anchor["exact_text"]) for anchor in record["gold_evidence"])


def test_complete_human_records_can_be_applied(tmp_path: Path) -> None:
    copied = tmp_path / "draft"
    shutil.copytree(CORPUS, copied)
    _, cases, _, _, _ = load_corpus(copied)
    reviews = []
    adjudications = []
    for case in cases:
        anchor_ids = [anchor.id for anchor in case.gold_evidence]
        review = ReviewRecord(
            review_id=f"review-{case.id}",
            case_id=case.id,
            reviewer_id="human-bilingual-01",
            reviewer_role="bilingual_primary",
            reviewed_outcome=case.expected_outcome,
            approved_anchor_ids=anchor_ids,
            reviewed_correction_required=case.correction.required,
            confidence="high",
            decision="approved",
            notes="Test fixture standing in for an explicit accountable human decision.",
            reviewed_at="2026-08-13T12:00:00+00:00",
        )
        reviews.append(review)
        if case.category in MANDATORY_ADJUDICATION_CATEGORIES:
            adjudications.append(
                AdjudicationRecord(
                    adjudication_id=f"adjudication-{case.id}",
                    case_id=case.id,
                    review_id=review.review_id,
                    adjudicator_id="human-safety-02",
                    adjudicator_role="safety_adjudicator",
                    original_outcome=case.expected_outcome,
                    dispute_reason="Mandatory safety adjudication in the corpus protocol.",
                    adjudicated_outcome=case.expected_outcome,
                    approved_anchor_ids=anchor_ids,
                    adjudicated_correction_required=case.correction.required,
                    decision="approved",
                    notes="Independent test adjudication.",
                    adjudicated_at="2026-08-13T13:00:00+00:00",
                )
            )
    review_path = tmp_path / "reviews.jsonl"
    adjudication_path = tmp_path / "adjudications.jsonl"
    review_path.write_text("".join(record.model_dump_json() + "\n" for record in reviews), encoding="utf-8")
    adjudication_path.write_text("".join(record.model_dump_json() + "\n" for record in adjudications), encoding="utf-8")
    applied = apply_review_records(copied, review_path, adjudication_path)
    assert applied.approved_cases == EXPECTED_CASES


def test_locked_checksum_tamper_detection(tmp_path: Path) -> None:
    copied = tmp_path / "draft"
    shutil.copytree(CORPUS, copied)
    checksum_entries = []
    from crag.corpus import CorpusStatus, _aggregate, _checksum_entries

    metadata, _, _, _, _ = load_corpus(copied)
    metadata.status = CorpusStatus.LOCKED
    metadata.aggregate_sha256 = None
    (copied / "corpus.json").write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
    checksum_entries = _checksum_entries(copied)
    metadata.aggregate_sha256 = _aggregate(checksum_entries)
    (copied / "corpus.json").write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
    checksum_entries = _checksum_entries(copied)
    (copied / "checksums.sha256").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksum_entries), encoding="utf-8"
    )
    assert verify_locked_corpus(copied) == []
    with (copied / "runtime_cases.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    assert verify_locked_corpus(copied)
