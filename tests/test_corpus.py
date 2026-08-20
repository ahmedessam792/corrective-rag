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
    ReviewProtocol,
    ReviewRecord,
    apply_review_records,
    audit_corpus,
    compile_runtime_manifest,
    load_corpus,
    lock_corpus,
    prepare_adjudication_review_batches,
    prepare_primary_review_batches,
    verify_locked_corpus,
)

CORPUS = Path("evaluation/corpora/crag-gold-v1-draft")


def test_draft_corpus_is_lock_eligible_under_revised_protocol() -> None:
    audit = audit_corpus(CORPUS, verify_documents=True)
    assert audit.total_cases == EXPECTED_CASES
    assert audit.structurally_complete_cases == EXPECTED_CASES
    assert audit.review_protocol == ReviewProtocol.PRIMARY_HUMAN_PLUS_MACHINE_AUDIT
    assert audit.approved_cases == EXPECTED_CASES
    assert audit.primary_reviewed_cases == EXPECTED_CASES
    assert audit.machine_audited_cases == 40
    assert audit.adjudicated_cases == 0
    assert not audit.missing_sources
    assert not audit.integrity_errors
    assert not audit.case_errors
    assert not audit.unresolved_reviews
    assert not audit.unresolved_adjudications
    assert not audit.unresolved_machine_audits
    assert not audit.protocol_errors
    assert audit.lock_eligible
    assert audit.verdict == "Corpus review complete and lock-eligible"
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


def test_lock_refuses_missing_primary_review(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    reviews = (copied / "reviews.jsonl").read_text(encoding="utf-8").splitlines()
    (copied / "reviews.jsonl").write_text("\n".join(reviews[1:]) + "\n", encoding="utf-8")
    audit = audit_corpus(copied, verify_documents=False)
    assert not audit.lock_eligible
    assert len(audit.unresolved_reviews) == 1
    with pytest.raises(RuntimeError, match="selected review protocol"):
        lock_corpus(copied, tmp_path / "crag-gold-v1")


def test_machine_audit_protocol_refuses_missing_or_stale_evidence(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    shutil.copytree(CORPUS, missing)
    (missing / "machine_audit.json").unlink()
    missing_audit = audit_corpus(missing, verify_documents=False)
    assert not missing_audit.lock_eligible
    assert "machine audit manifest is missing" in missing_audit.protocol_errors

    stale = tmp_path / "stale"
    shutil.copytree(CORPUS, stale)
    reviews = stale / "reviews.jsonl"
    records = [json.loads(line) for line in reviews.read_text(encoding="utf-8").splitlines()]
    records[0]["notes"] += " Stale post-audit edit."
    reviews.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    stale_audit = audit_corpus(stale, verify_documents=False)
    assert not stale_audit.lock_eligible
    assert any("checksums are stale" in error for error in stale_audit.protocol_errors)


def test_audit_detects_source_tampering(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    source = next((copied / "fixtures").glob("*.docx"))
    source.write_bytes(source.read_bytes() + b"tampered")
    audit = audit_corpus(copied, verify_documents=False)
    assert any("source hash mismatch" in error for error in audit.integrity_errors)
    assert not audit.lock_eligible


def test_audit_detects_anchor_hash_tampering(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    manifest = copied / "gold_cases.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    records[0]["gold_evidence"][0]["normalized_text_sha256"] = "0" * 64
    manifest.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    audit = audit_corpus(copied, verify_documents=False)
    assert any("passage hash is invalid" in error for errors in audit.case_errors.values() for error in errors)
    assert not audit.lock_eligible


def test_audit_rejects_gold_leakage_in_runtime_manifest(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    runtime = copied / "runtime_cases.jsonl"
    records = [json.loads(line) for line in runtime.read_text(encoding="utf-8").splitlines()]
    records[0]["expected_outcome"] = "SUPPORTED"
    runtime.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    audit = audit_corpus(copied, verify_documents=False)
    assert any("runtime line 1" in error for error in audit.integrity_errors)
    assert not audit.lock_eligible


def test_unsupported_review_protocol_is_rejected(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    metadata_path = copied / "corpus.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["review_protocol"] = "automatic_approval"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="review_protocol"):
        audit_corpus(copied, verify_documents=False)


def test_two_human_protocol_still_requires_independent_adjudication(tmp_path: Path) -> None:
    copied = tmp_path / "strict"
    shutil.copytree(CORPUS, copied)
    metadata, _, _, _, _ = load_corpus(copied)
    metadata.review_protocol = ReviewProtocol.TWO_HUMAN_ADJUDICATION
    metadata.machine_audit_manifest = None
    metadata.review_methodology = None
    metadata.review_limitations = []
    (copied / "corpus.json").write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
    audit = audit_corpus(copied, verify_documents=False)
    assert audit.approved_cases == 20
    assert len(audit.unresolved_adjudications) == 40
    assert audit.machine_audited_cases == 0
    assert not audit.protocol_errors
    assert not audit.lock_eligible


def test_arabic_questions_and_evidence_are_nfc() -> None:
    import unicodedata

    for line in (CORPUS / "gold_cases.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["language"] != "ar":
            continue
        assert unicodedata.is_normalized("NFC", record["question"])
        assert all(unicodedata.is_normalized("NFC", anchor["exact_text"]) for anchor in record["gold_evidence"])


def test_primary_review_batches_are_complete_and_do_not_mutate_corpus(tmp_path: Path) -> None:
    protected = {
        name: (CORPUS / name).read_bytes()
        for name in ("gold_cases.jsonl", "reviews.jsonl", "adjudications.jsonl", "runtime_cases.jsonl")
    }
    output = prepare_primary_review_batches(CORPUS, tmp_path / "primary", verify_documents=False)
    index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    assert index["stage"] == "primary"
    assert index["case_count"] == EXPECTED_CASES
    assert len(index["batches"]) == 6
    assert all(len(batch["case_ids"]) == 10 for batch in index["batches"])
    case_ids = [case_id for batch in index["batches"] for case_id in batch["case_ids"]]
    assert len(case_ids) == len(set(case_ids)) == EXPECTED_CASES
    for batch in index["batches"]:
        packet = json.loads((output / f"{batch['batch_id']}.packet.json").read_text(encoding="utf-8"))
        assert {case["language"] for case in packet["cases"]} == {"en", "ar"}
        assert all(case["sources"] for case in packet["cases"])
        assert all("expected_outcome" in case["proposal"] for case in packet["cases"])
        assert (output / f"{batch['batch_id']}.md").is_file()
        assert (output / f"{batch['batch_id']}.reviews.template.jsonl").is_file()
    assert prepare_primary_review_batches(CORPUS, output, verify_documents=False) == output
    first_template = output / f"{index['batches'][0]['batch_id']}.reviews.template.jsonl"
    first_template.write_text(first_template.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="preserve it"):
        prepare_primary_review_batches(CORPUS, output, verify_documents=False)
    for name, original in protected.items():
        assert (CORPUS / name).read_bytes() == original


def test_adjudication_batches_refuse_to_preempt_primary_review(tmp_path: Path) -> None:
    copied = tmp_path / "draft-without-primary-records"
    shutil.copytree(CORPUS, copied)
    (copied / "reviews.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="completed primary records"):
        prepare_adjudication_review_batches(copied, tmp_path / "adjudication")


def test_complete_human_records_can_be_applied(tmp_path: Path) -> None:
    copied = tmp_path / "draft"
    shutil.copytree(CORPUS, copied)
    metadata, cases, _, _, _ = load_corpus(copied)
    metadata.review_protocol = ReviewProtocol.TWO_HUMAN_ADJUDICATION
    metadata.machine_audit_manifest = None
    metadata.review_methodology = None
    metadata.review_limitations = []
    (copied / "corpus.json").write_text(metadata.model_dump_json(indent=2) + "\n", encoding="utf-8")
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
                    confidence="high",
                    decision="confirm_primary",
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
    assert applied.adjudicated_cases == 40
    assert applied.lock_eligible
    output = prepare_adjudication_review_batches(copied, tmp_path / "adjudication")
    index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    assert index["case_count"] == 40
    assert len(index["batches"]) == 4
    assert all((output / f"{batch['batch_id']}.md").is_file() for batch in index["batches"])
    assert all(len(batch["case_ids"]) == 10 for batch in index["batches"])
    for batch in index["batches"]:
        packet = json.loads((output / f"{batch['batch_id']}.packet.json").read_text(encoding="utf-8"))
        assert all(case["adjudication_requirement"] for case in packet["cases"])
        assert all("primary_review" in case for case in packet["cases"])
        assert "Codex" not in (output / f"{batch['batch_id']}.md").read_text(encoding="utf-8")
        templates = [
            json.loads(line)
            for line in (output / f"{batch['batch_id']}.adjudications.template.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert all("confidence" in record for record in templates)
        assert all("CONFIRM_PRIMARY" in record["decision"] for record in templates)


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
