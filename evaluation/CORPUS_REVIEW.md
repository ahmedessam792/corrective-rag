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

## Final safety/dispute audit protocol

The final Phase 6D protocol adopted for this corpus is:

> **60/60 Primary Human Review + 40/40 Independent Machine-Assisted Safety/Dispute Audit**

**No independent second-human adjudication was performed.** The primary bilingual human reviewer made
the accountable gold decisions for all 60 cases. A separate machine-assisted audit then re-opened the
physical sources for every `PARTIAL`, `INSUFFICIENT`, `CONTRADICTORY`, and prompt-injection case and checked
source absence, support, conflict resolution, injection isolation, hashes, anchors, correction flags,
bilingual consistency, and leakage boundaries.

Machine findings are evaluator-only audit evidence, not human adjudications. They must not populate
`adjudications.jsonl`, use a human reviewer identity, or be described as second-human approval. The detailed
advisory report and final lock-readiness audit are preserved under `evaluation/pre-review/`.

The previously generated adjudication packets remain available if a future release elects to require a
second human. They are not completed records for this corpus version.

## Approval and leakage

Completed review files are evaluator-only. Never copy labels, anchors, correction metadata, notes, or
review records into `runtime_cases.jsonl`, source documents, prompts, retrieval metadata, rewriting,
verification, or generation inputs. `corpus-apply-reviews` rejects placeholder or automation identities;
`corpus-audit` checks review consistency and the runtime allow-list.

The 2026-08-20 audit found 40/40 safety/dispute cases semantically valid, zero corpus defects, zero false
`SUPPORTED` labels, zero integrity errors, and no leakage. Phase 6D is complete under the revised protocol.
The corpus is eligible for locking under that protocol, but the legacy lock guard still requires explicit
second-human records. Do not bypass it or fabricate records: align the lock gate with the documented,
checksum-bound machine audit in a separate explicit step, then verify the locked checksum set before Phase 6E.
