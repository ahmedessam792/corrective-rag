# CRAG Gold v1 Phase 6D Lock-Readiness Audit

Date: 2026-08-20  
Corpus: `crag-gold-v1-draft`  
Status: **machine-assisted audit evidence; not a human adjudication record**

## Final review protocol

The final Phase 6D review protocol for this corpus is:

> **60/60 Primary Human Review + 40/40 Independent Machine-Assisted Safety/Dispute Audit**

**No independent second-human adjudication was performed.** The machine-assisted audit did not populate
`adjudications.jsonl`, did not assume a human identity, and must not be described as human adjudication.

## Bound evidence

- Gold manifest SHA-256: `e164eacaf10a63507a47cd7603d72fc3ff18e81549994194d88068ef53e57d6d`
- Source manifest SHA-256: `3e38522048e25e49b42ded778afbd270cd627385406e30954d0489675c99d5bb`
- Primary review manifest SHA-256: `32399df18abc0fd5a9521e1d8ed928a91369981c71816a65a4c3d1d1b144b96a`
- Detailed machine pre-review SHA-256: `7a126d0bd7d58b99db287cb40a8d32db9888c8a38c9a36e886e1745bcac6053f`

## Audit scope and result

All 40 pending safety/dispute-sensitive cases were re-opened from their physical PDF/DOCX fixtures.
The audit checked complete-source absence, partial support and absence, both sides of every conflict,
authority/version/date/supersession signals, prompt-injection isolation, source and passage hashes,
anchor locations, source linkage, correction flags, English/Arabic pairing, runtime/gold separation,
review uniqueness/currentness, the six revision-2 cases, and the frozen corpus distribution.

- Cases audited: **40/40**
- Confirmed semantically valid: **40/40**
- Genuine defects: **0**
- Unresolved underlying facts due to intentional contradiction: **10**
- False `SUPPORTED`: **0**
- Integrity errors: **0**
- Leakage: **none**
- Source or anchor failures: **0**
- Duplicate or stale primary records: **0**
- Official human adjudication records: **0/40**

The ten contradiction cases contain two materially incompatible approved statements. The counter-sources
are described as current governance records, but no source provides an explicit supersession, precedence,
replacement, effective-revision, or authority rule. Selecting either statement would therefore require an
unstated assumption. `CONTRADICTORY` remains the defensible gold outcome for all ten cases.

No case failed the audit, so there is no non-clean-case table.

## Lock readiness

The corpus is semantically and structurally eligible for locking **under the revised review protocol**.
The existing `corpus-lock` implementation still enforces the superseded requirement for 40 official
second-human adjudication records and will correctly refuse the current draft. That tooling mismatch is
not a corpus defect, but it must be resolved explicitly before running the lock command. The lock gate must
recognize and checksum this revised protocol and its machine-audit evidence without fabricating human
adjudications or weakening source, integrity, review, or leakage checks.

No lock was attempted and Phase 6E was not started.

## Verdict

**Phase 6D complete under revised review protocol**
