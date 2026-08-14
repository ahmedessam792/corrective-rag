# Bilingual gold-corpus review protocol

## Roles and order

The primary reviewer uses a stable human identifier and is fluent in English and Arabic. For every case,
the reviewer opens every listed PDF or DOCX, reads the question, and independently records the outcome,
atomic claims, exact evidence anchors, correction intent, confidence, uncertainty, and notes. AI or tool
suggestions may help locate passages but cannot supply the approval decision.

Review source files before comparing the proposed evaluator metadata. If the source is unnatural,
ambiguous, inaccessible, or does not create the intended condition, return the case to draft and revise
the source specification. Rebuild and repeat review after any source change.

Generate the primary packets with `validate.py corpus-prepare-review-batches --stage primary`. There are
six bilingual batches of ten cases, one batch per frozen category. Review the English and Arabic cases in
each batch directly against their linked fixtures and complete the companion JSONL response template.
The proposed values remain visible so amendments can be recorded explicitly; they are never implicit
approval. Preserve every completed primary record even when the decision is `changes_required`.

## Outcome rules

- `SUPPORTED`: all material answer components are directly supported by necessary or legitimate
  alternative evidence, with no unresolved verified conflict.
- `PARTIAL`: at least one independently useful component is supported and at least one requested
  component is absent. The final system may release only the supported component and must disclose the
  missing portion.
- `INSUFFICIENT`: the case sources do not contain evidence for the requested fact. Approval requires an
  explicit all-case-source absence assertion; related context is not sufficient support.
- `CONTRADICTORY`: two verified sources make materially incompatible claims and the case provides no
  authoritative resolution. Both conflicting passages are required gold evidence.

`correction.required` describes corpus design intent, not a measured retriever result. Approve it only
when a bridge passage maps the question's generic, legacy, acronym, or synonymous wording to the
controlled term needed for the target passage. Do not test or tune retrieval against these cases during
review.

## Adjudication

A second person with a different stable identifier adjudicates all `PARTIAL`, `INSUFFICIENT`,
`CONTRADICTORY`, and prompt-injection cases. Adjudication is also required for medium/low confidence,
any requested label change, ambiguous citation support, or a `SUPPORTED` versus `INSUFFICIENT` dispute.
The adjudicator records the original outcome, dispute or mandatory-safety reason, final outcome, final
anchors, correction decision, and notes. Original review records are preserved.

Only after primary records are applied, generate the second-review packets with
`validate.py corpus-prepare-review-batches --stage adjudication`. The command refuses missing primary
records and unresolved `changes_required` cases. The adjudicator packet includes the original primary
record, but the second reviewer must still inspect the source independently and use a different stable
human identifier.

## Approval and leakage

Completed review files are evaluator-only. Never copy labels, anchors, correction metadata, notes, or
review records into `runtime_cases.jsonl`, source documents, prompts, retrieval metadata, rewriting,
verification, or generation inputs. `corpus-apply-reviews` rejects placeholder or automation identities;
`corpus-audit` checks review consistency and the runtime allow-list.

The only Phase 6D ready verdict is `Gold corpus locked and benchmark-ready`. Until the locked checksum
set verifies, Phase 6E must not start.
