# Primary review batch: primary-01-answerable

Corpus: `crag-bilingual-gold` / `crag-gold-v1-draft`

This packet contains evaluator-only proposals. Inspect every source directly before deciding. Do not treat the proposal or any model assistance as approved truth.

## ar-answerable-01

- Language: `ar`
- Question: ما القرار الذي تسمح به السياسة؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-ar-policy-a-v1` — سياسة العمل المرن; `fixtures/ar-policy-a.pdf`; version `1.0`; SHA-256 `aab21646c8e263d5e289e401e4979134d22b3c625bca8de88fbbb3317682c74f`

Proposed atomic claims:

- `ar-answerable-01-claim-1` (`supported`): يجوز لرؤساء الإدارات الموافقة على العمل عن بعد لمدة لا تتجاوز يومين أسبوعياً.

Proposed evidence anchors:

- `ar-answerable-01-ev-support` — source `src-ar-policy-a-v1`, role `necessary`, page 1, characters 127-213
  - Exact passage: “تسمح السياسة لرؤساء الإدارات بالموافقة على العمل عن بعد لمدة لا تتجاوز يومين أسبوعياً.”
  - Passage SHA-256: `b648d63201656714b6cec3611ec6d0e1f184dd162f3a87ae62f8a5ea84c6d747`
  - Claims: `ar-answerable-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-answerable-02

- Language: `ar`
- Question: ما التاريخ المذكور في التقرير؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-ar-report-a-v1` — تقرير العمليات ربع السنوي; `fixtures/ar-report-a.docx`; version `1.0`; SHA-256 `f8401cfaf9b2a36e2a9ac93f5770aa87e460a8336e4af5c866b9243e681a3dee`

Proposed atomic claims:

- `ar-answerable-02-claim-1` (`supported`): يحدد التقرير تاريخ الثلاثين من يونيو عام ألفين وخمسة وعشرين.

Proposed evidence anchors:

- `ar-answerable-02-ev-support` — source `src-ar-report-a-v1`, role `necessary`, heading السجل المعتمد, paragraph 4, characters 0-63
  - Exact passage: “انتهت فترة التقرير في الثلاثين من يونيو عام ألفين وخمسة وعشرين.”
  - Passage SHA-256: `de2fe300ac1f5f2b299f01c3152d0488ce12193cc9c0c5adebcfded77f7a629c`
  - Claims: `ar-answerable-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-answerable-03

- Language: `ar`
- Question: ما القيد الذي توضحه الدراسة؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-ar-study-a-v1` — دراسة سير العمل السريري; `fixtures/ar-study-a.pdf`; version `1.0`; SHA-256 `40b1c84029a26d611875f9ddc1314485030ff9c7e22a2638d1899d6457c50377`

Proposed atomic claims:

- `ar-answerable-03-claim-1` (`supported`): جُمعت جميع الملاحظات من مستشفى واحد فقط.

Proposed evidence anchors:

- `ar-answerable-03-ev-support` — source `src-ar-study-a-v1`, role `necessary`, page 1, characters 133-198
  - Exact passage: “يتمثل القيد الرئيس في أن جميع الملاحظات جُمعت من مستشفى واحد فقط.”
  - Passage SHA-256: `a1f83374fb2308c46b95e3356cdcd45e20d9e28ab0e7196e10b2b68deda24620`
  - Claims: `ar-answerable-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-answerable-04

- Language: `ar`
- Question: من المسؤول عن الإجراء الموثق؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-ar-process-a-v1` — إجراء مراجعة التغيير; `fixtures/ar-process-a.docx`; version `1.0`; SHA-256 `01714e15e6b19a4f52790271310b1f5a6f9f2f9897a8c94986de0ccdceb757d3`

Proposed atomic claims:

- `ar-answerable-04-claim-1` (`supported`): مكتب ضمان الجودة هو المسؤول عن الإجراء.

Proposed evidence anchors:

- `ar-answerable-04-ev-support` — source `src-ar-process-a-v1`, role `necessary`, heading السجل المعتمد, paragraph 4, characters 0-53
  - Exact passage: “يتولى مكتب ضمان الجودة مسؤولية إجراء المراجعة الموثق.”
  - Passage SHA-256: `a7d4f032a792ecc73ebabb582ae24320f198cce8a6d62115c14a9cbec160b265`
  - Claims: `ar-answerable-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-answerable-05

- Language: `ar`
- Question: ما الحد المذكور في المصدر؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-ar-technical-a-v1` — معيار موثوقية الخدمة; `fixtures/ar-technical-a.pdf`; version `1.0`; SHA-256 `b1c2f7626370a3f72a94b8e0182c2296303ce8ecaa9a876d55620764fb99346c`

Proposed atomic claims:

- `ar-answerable-05-claim-1` (`supported`): الحد هو خمسة وثمانون في المئة.

Proposed evidence anchors:

- `ar-answerable-05-ev-support` — source `src-ar-technical-a-v1`, role `necessary`, page 1, characters 117-182
  - Exact passage: “يلزم التصعيد عندما تنخفض درجة الموثوقية عن خمسة وثمانين في المئة.”
  - Passage SHA-256: `e7d751cad076a33774b57c0163838f3ce653279f6e44013b2926d8a20b5c9ca9`
  - Claims: `ar-answerable-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-answerable-01

- Language: `en`
- Question: What decision does the policy authorize?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-en-policy-a-v1` — Flexible Work Policy; `fixtures/en-policy-a.pdf`; version `1.0`; SHA-256 `3494a51282883250be8e19b1f5744660e28343a110eab7f0f930f41e98dd3672`

Proposed atomic claims:

- `en-answerable-01-claim-1` (`supported`): Department heads may approve remote work for up to two days per week.

Proposed evidence anchors:

- `en-answerable-01-ev-support` — source `src-en-policy-a-v1`, role `necessary`, page 1, characters 150-240
  - Exact passage: “The policy authorizes department heads to approve remote work for up to two days per week.”
  - Passage SHA-256: `cd48b9c4917d0f9cf9a9fbc960acc019d6de5fe9abf566dfafe20421cd1b71dc`
  - Claims: `en-answerable-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-answerable-02

- Language: `en`
- Question: Which date does the report identify?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-en-report-a-v1` — Quarterly Operations Report; `fixtures/en-report-a.docx`; version `1.0`; SHA-256 `363278656ce67ad1a769377227a6bff7df3637428b97cb4cbc23324a9902310f`

Proposed atomic claims:

- `en-answerable-02-claim-1` (`supported`): The report identifies 30 June 2025.

Proposed evidence anchors:

- `en-answerable-02-ev-support` — source `src-en-report-a-v1`, role `necessary`, heading Approved record, paragraph 4, characters 0-44
  - Exact passage: “The reporting period closed on 30 June 2025.”
  - Passage SHA-256: `7275c081f0c70ccda5bf35cdae9a8a20f9ec72b535d19ee4f2b65d7a5b3f0c7e`
  - Claims: `en-answerable-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-answerable-03

- Language: `en`
- Question: What limitation does the study report?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-en-study-a-v1` — Clinical Workflow Study; `fixtures/en-study-a.pdf`; version `1.0`; SHA-256 `b950177f2fa41fb8f1976c7b28837243df8585e4df8da273da7415d349d63840`

Proposed atomic claims:

- `en-answerable-03-claim-1` (`supported`): All observations came from a single hospital.

Proposed evidence anchors:

- `en-answerable-03-ev-support` — source `src-en-study-a-v1`, role `necessary`, page 1, characters 156-234
  - Exact passage: “The principal limitation is that all observations came from a single hospital.”
  - Passage SHA-256: `f9a8d0b86c354eb0179406802fcf6a227babe835fce487a7f68150f60499cb5b`
  - Claims: `en-answerable-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-answerable-04

- Language: `en`
- Question: Who owns the documented process?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-en-process-a-v1` — Change Review Procedure; `fixtures/en-process-a.docx`; version `1.0`; SHA-256 `ea2ab538b6ddc48c08615627b539a07235007fd03a2312c5d49702a6490995a7`

Proposed atomic claims:

- `en-answerable-04-claim-1` (`supported`): The Quality Assurance Office owns the process.

Proposed evidence anchors:

- `en-answerable-04-ev-support` — source `src-en-process-a-v1`, role `necessary`, heading Approved record, paragraph 4, characters 0-64
  - Exact passage: “The Quality Assurance Office owns the documented review process.”
  - Passage SHA-256: `c0535afbdd55c038ef3b5efa31b36d6229458dd089d6c05f077ca1b4ed158564`
  - Claims: `en-answerable-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-answerable-05

- Language: `en`
- Question: What threshold appears in the source?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `false`

Sources:

- `src-en-technical-a-v1` — Service Reliability Standard; `fixtures/en-technical-a.pdf`; version `1.0`; SHA-256 `86224de07cb4a5ee96b9b15e32c7f7b47ff2ba061b01fd79e42849a4b941d6b3`

Proposed atomic claims:

- `en-answerable-05-claim-1` (`supported`): The threshold is 85 percent.

Proposed evidence anchors:

- `en-answerable-05-ev-support` — source `src-en-technical-a-v1`, role `necessary`, page 1, characters 159-232
  - Exact passage: “Escalation is required when the reliability score falls below 85 percent.”
  - Passage SHA-256: `93f50dc062c68fdbcbc42feb453d2a090983f29838499ffc0007353a812cc39b`
  - Claims: `en-answerable-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:
