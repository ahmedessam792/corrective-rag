# Adjudication evidence batch: adjudication-04-partial

Corpus: `crag-bilingual-gold` / `crag-gold-v1-draft`

This packet contains evaluator-only proposals. Inspect every source directly before deciding. Do not treat the proposal or any model assistance as approved truth.

## ar-partial-01

- Language: `ar`
- Question: اذكر الحد المعتمد وتاريخ تنفيذه.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: تاريخ التنفيذ غير مذكور.

Sources:

- `src-ar-policy-c-v1` — حد النقل المعتمد; `fixtures/ar-policy-c.pdf`; version `1.0`; SHA-256 `580eda234c757c66f51caa071473d8d1d57d4f0f3d50f2796c950a279741e846`

Proposed atomic claims:

- `ar-partial-01-claim-1` (`supported`): الحد المعتمد هو مئتان وخمسون سجلاً لكل عملية نقل.
- `ar-partial-01-claim-2` (`absent`): تاريخ التنفيذ غير مذكور.

Proposed evidence anchors:

- `ar-partial-01-ev-support` — source `src-ar-policy-c-v1`, role `necessary`, page 1, characters 61-117
  - Exact passage: “الحد المعتمد للدفعة هو مئتان وخمسون سجلاً لكل عملية نقل.”
  - Passage SHA-256: `f9ef2b6630f73898684eb566747ccb9d5deea957eade7effe054bc4739dd68bb`
  - Claims: `ar-partial-01-claim-1`
## ar-partial-02

- Language: `ar`
- Question: من وافق على الإجراء ولماذا؟
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: سبب الاعتماد غير مسجل.

Sources:

- `src-ar-process-c-v1` — سجل اعتماد الإجراء; `fixtures/ar-process-c.docx`; version `1.0`; SHA-256 `e5216cdded2fd057fa82a563ed8d005fcd373c4eee8ee76d881d4b4420b473bb`

Proposed atomic claims:

- `ar-partial-02-claim-1` (`supported`): اعتمد مدير العمليات الإجراء.
- `ar-partial-02-claim-2` (`absent`): سبب الاعتماد غير مسجل.

Proposed evidence anchors:

- `ar-partial-02-ev-support` — source `src-ar-process-c-v1`, role `necessary`, heading السجل المعتمد, paragraph 3, characters 0-35
  - Exact passage: “اعتمد مدير العمليات الإجراء المعدل.”
  - Passage SHA-256: `0a3751a44a3aab15e43650b1bee538a5c560b43765e5cd5234a4e550cd997a5d`
  - Claims: `ar-partial-02-claim-1`
## ar-partial-03

- Language: `ar`
- Question: اذكر النتيجة المقاسة وحجم البيانات الخام.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: حجم البيانات الخام غير مذكور.

Sources:

- `src-ar-study-b-v1` — دراسة خفض قوائم الانتظار; `fixtures/ar-study-b.pdf`; version `1.0`; SHA-256 `8dd0cedbcbf12b724a80388b6eeb77a18b456839709eca2da532a7f292440376`

Proposed atomic claims:

- `ar-partial-03-claim-1` (`supported`): كانت النتيجة المقاسة انخفاضاً بنسبة ثمانية عشر في المئة في الوسيط الزمني للانتظار.
- `ar-partial-03-claim-2` (`absent`): حجم البيانات الخام غير مذكور.

Proposed evidence anchors:

- `ar-partial-03-ev-support` — source `src-ar-study-b-v1`, role `necessary`, page 1, characters 69-141
  - Exact passage: “حقق التدخل انخفاضاً بنسبة ثمانية عشر في المئة في الوسيط الزمني للانتظار.”
  - Passage SHA-256: `a9b19ecf08c6b0792b7f5666804d1b204b94767ee04b6afdb69489a53920a495`
  - Claims: `ar-partial-03-claim-1`
## ar-partial-04

- Language: `ar`
- Question: صف الضابط وتكلفة شرائه.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: تكلفة الشراء غير مذكورة.

Sources:

- `src-ar-security-b-v1` — ضابط مراجعة الوصول; `fixtures/ar-security-b.docx`; version `1.0`; SHA-256 `c2369ea670bd101cc22cabc4f135e13a2490833b30ebc3e91b44268f31aa2403`

Proposed atomic claims:

- `ar-partial-04-claim-1` (`supported`): الضابط هو مراجعة فصلية لصلاحيات الوصول المميز.
- `ar-partial-04-claim-2` (`absent`): تكلفة الشراء غير مذكورة.

Proposed evidence anchors:

- `ar-partial-04-ev-support` — source `src-ar-security-b-v1`, role `necessary`, heading السجل المعتمد, paragraph 3, characters 0-49
  - Exact passage: “يتطلب الضابط مراجعة فصلية لصلاحيات الوصول المميز.”
  - Passage SHA-256: `70e15814d764652bf8ce85f2afc1f28179fdc9c5bb13d0c1b03e86b94f979a09`
  - Claims: `ar-partial-04-claim-1`
## ar-partial-05

- Language: `ar`
- Question: ما الذي تغير ومن طلب التغيير؟
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: الجهة الطالبة غير محددة.

Sources:

- `src-ar-report-b-v1` — إشعار تغيير مدة الاحتفاظ; `fixtures/ar-report-b.pdf`; version `1.0`; SHA-256 `84d7993f38b4c604f080227d265d72db03de5ab74c05d48adec76afa29c6ae60`

Proposed atomic claims:

- `ar-partial-05-claim-1` (`supported`): تغيرت مدة الاحتفاظ من ثلاث سنوات إلى خمس سنوات.
- `ar-partial-05-claim-2` (`absent`): الجهة الطالبة غير محددة.

Proposed evidence anchors:

- `ar-partial-05-ev-support` — source `src-ar-report-b-v1`, role `necessary`, page 1, characters 69-116
  - Exact passage: “تغيرت مدة الاحتفاظ من ثلاث سنوات إلى خمس سنوات.”
  - Passage SHA-256: `c88e0e57daf4b0624790d0454b0bcaa6fd18a5409f4d4f45a5a7a082e195e112`
  - Claims: `ar-partial-05-claim-1`
## en-partial-01

- Language: `en`
- Question: State the approved limit and its implementation date.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: The implementation date is not stated.

Sources:

- `src-en-policy-c-v1` — Approved Transfer Limit; `fixtures/en-policy-c.pdf`; version `1.0`; SHA-256 `42e050d3a3d0c402d374c6aabb6018aa6110800d7d652760d9c5262c02b5e93c`

Proposed atomic claims:

- `en-partial-01-claim-1` (`supported`): The approved limit is 250 records per transfer.
- `en-partial-01-claim-2` (`absent`): The implementation date is not stated.

Proposed evidence anchors:

- `en-partial-01-ev-support` — source `src-en-policy-c-v1`, role `necessary`, page 1, characters 83-136
  - Exact passage: “The approved batch limit is 250 records per transfer.”
  - Passage SHA-256: `7370faa2717de547d355399b2a3405d5ddd8dee7f7a20030e2aef51b78f3a82d`
  - Claims: `en-partial-01-claim-1`
## en-partial-02

- Language: `en`
- Question: Who approved the process and why?
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: The reason for approval is not recorded.

Sources:

- `src-en-process-c-v1` — Process Approval Record; `fixtures/en-process-c.docx`; version `1.0`; SHA-256 `ba45fdb27641af57d9a945c6c0d844adb3645e84fa0fc496d579f72d24b2d51f`

Proposed atomic claims:

- `en-partial-02-claim-1` (`supported`): The Operations Director approved the process.
- `en-partial-02-claim-2` (`absent`): The reason for approval is not recorded.

Proposed evidence anchors:

- `en-partial-02-ev-support` — source `src-en-process-c-v1`, role `necessary`, heading Approved record, paragraph 3, characters 0-53
  - Exact passage: “The Operations Director approved the revised process.”
  - Passage SHA-256: `da977e7af2f4d09ec6f5224842408fb87813e2c42233a5843a69a4b96fcd9f60`
  - Claims: `en-partial-02-claim-1`
## en-partial-03

- Language: `en`
- Question: Give the measured result and the raw dataset size.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: The raw dataset size is not reported.

Sources:

- `src-en-study-b-v1` — Queue Reduction Study; `fixtures/en-study-b.pdf`; version `1.0`; SHA-256 `1a517d44370f93d89717f9fca75c5b42ee17c733ec790695a95ae2e1343d6559`

Proposed atomic claims:

- `en-partial-03-claim-1` (`supported`): The measured result was an 18 percent reduction in median queue time.
- `en-partial-03-claim-2` (`absent`): The raw dataset size is not reported.

Proposed evidence anchors:

- `en-partial-03-ev-support` — source `src-en-study-b-v1`, role `necessary`, page 1, characters 81-152
  - Exact passage: “The intervention produced an 18 percent reduction in median queue time.”
  - Passage SHA-256: `17d0fdbf779095800544c000063707165b9d29c84be6f2fa21201e5cd0261d18`
  - Claims: `en-partial-03-claim-1`
## en-partial-04

- Language: `en`
- Question: Describe the control and its procurement cost.
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: The procurement cost is not provided.

Sources:

- `src-en-security-b-v1` — Access Review Control; `fixtures/en-security-b.docx`; version `1.0`; SHA-256 `389b2d5a39153522c6ea2089323579079b7199e263b0d77e6631ce71bebd70b0`

Proposed atomic claims:

- `en-partial-04-claim-1` (`supported`): The control is a quarterly review of privileged access.
- `en-partial-04-claim-2` (`absent`): The procurement cost is not provided.

Proposed evidence anchors:

- `en-partial-04-ev-support` — source `src-en-security-b-v1`, role `necessary`, heading Approved record, paragraph 3, characters 0-61
  - Exact passage: “The control requires a quarterly review of privileged access.”
  - Passage SHA-256: `0978b4843d074424ca3120138dd870eec5740db5b01e9977d942e31994679445`
  - Claims: `en-partial-04-claim-1`
## en-partial-05

- Language: `en`
- Question: What changed and who requested the change?
- Proposed outcome: `PARTIAL`
- Proposed correction required: `false`
- Missing information: The requester is not identified.

Sources:

- `src-en-report-b-v1` — Retention Change Notice; `fixtures/en-report-b.pdf`; version `1.0`; SHA-256 `672f394811927b09242789c637d2fdcaa4d6685d9d65201848ef9d563860314f`

Proposed atomic claims:

- `en-partial-05-claim-1` (`supported`): The retention period changed from three years to five years.
- `en-partial-05-claim-2` (`absent`): The requester is not identified.

Proposed evidence anchors:

- `en-partial-05-ev-support` — source `src-en-report-b-v1`, role `necessary`, page 1, characters 83-143
  - Exact passage: “The retention period changed from three years to five years.”
  - Passage SHA-256: `c7ff4d3e4d1ed0af94496e0f774071bac9d1ec6f0958b5fd4508ebc4aa638cc3`
  - Claims: `en-partial-05-claim-1`

# Preserved primary decisions

The adjudicator must independently inspect the sources. The records below preserve, but do not replace, that independent judgment.

## ar-partial-01 primary record

- Review ID: `primary-reviewer-01-ar-partial-01-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `ar-partial-01-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## ar-partial-02 primary record

- Review ID: `primary-reviewer-01-ar-partial-02-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `ar-partial-02-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## ar-partial-03 primary record

- Review ID: `primary-reviewer-01-ar-partial-03-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `ar-partial-03-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## ar-partial-04 primary record

- Review ID: `primary-reviewer-01-ar-partial-04-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `ar-partial-04-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## ar-partial-05 primary record

- Review ID: `primary-reviewer-01-ar-partial-05-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `ar-partial-05-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## en-partial-01 primary record

- Review ID: `primary-reviewer-01-en-partial-01-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `en-partial-01-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## en-partial-02 primary record

- Review ID: `primary-reviewer-01-en-partial-02-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `en-partial-02-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## en-partial-03 primary record

- Review ID: `primary-reviewer-01-en-partial-03-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `en-partial-03-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## en-partial-04 primary record

- Review ID: `primary-reviewer-01-en-partial-04-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `en-partial-04-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:

## en-partial-05 primary record

- Review ID: `primary-reviewer-01-en-partial-05-r1`
- Primary reviewer: `primary-reviewer-01`
- Decision: `approved`
- Reviewed outcome: `PARTIAL`
- Reviewed correction required: `false`
- Approved anchor IDs: `en-partial-05-ev-support`
- Confidence: `medium`
- Uncertainty: The supported portion is directly evidenced, but the missing portion should be independently confirmed as absent across the full referenced source before the PARTIAL label is treated as final.
- Notes: Approved with medium confidence after bilingual partial-evidence review; independent absence confirmation is required.
- Why adjudication is mandatory: Independent safety review must confirm both the supported portion and whole-source absence of the missing portion before a bounded PARTIAL answer is final. The primary record also contains confidence or uncertainty requiring independent resolution.

Adjudicator response (complete the companion JSONL record):

- Dispute or mandatory-safety reason:
- Adjudicated outcome:
- Approved anchor IDs:
- Adjudicated correction required:
- Confidence: `high` / `medium` / `low`
- Decision: `confirm_primary` / `change_required` / `unresolved`
- Notes:
