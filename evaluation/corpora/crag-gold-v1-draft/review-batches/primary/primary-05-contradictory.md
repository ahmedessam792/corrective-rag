# Primary review batch: primary-05-contradictory

Corpus: `crag-bilingual-gold` / `crag-gold-v1-draft`

This packet contains evaluator-only proposals. Inspect every source directly before deciding. Do not treat the proposal or any model assistance as approved truth.

## ar-conflict-01

- Language: `ar`
- Question: ما مدة الاحتفاظ المعتمدة؟
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-ar-conflict-retention-v1` — جدول الاحتفاظ - العمليات; `fixtures/ar-conflict-retention.pdf`; version `1.0`; SHA-256 `2b97499458e6143ac6e3ec195aafb5aee9803b0db325e3cc85c47fae968b9264`
- `src-ar-conflict-retention-counter-v1` — جدول الاحتفاظ - العمليات - الحوكمة; `fixtures/ar-conflict-retention-counter.pdf`; version `1.0`; SHA-256 `4b7e7bbfa2f478ab9608a717d4e31e15c5032de21831210b0bee448c249d8cb7`

Proposed atomic claims:

- `ar-conflict-01-claim-1` (`conflicted`): يذكر أحد المصدرين المعتمدين مدة خمس سنوات.

Proposed evidence anchors:

- `ar-conflict-01-ev-conflict-a` — source `src-ar-conflict-retention-v1`, role `conflicting`, page 1, characters 69-118
  - Exact passage: “مدة الاحتفاظ المعتمدة لسجلات الخدمة هي خمس سنوات.”
  - Passage SHA-256: `fb2dd506a5d4a3576adfba1cc99e4b140c3a5393fa7c70ddd6ad3b6c15cfd604`
  - Claims: `ar-conflict-01-claim-1`
- `ar-conflict-01-ev-conflict-b` — source `src-ar-conflict-retention-counter-v1`, role `conflicting`, page 1, characters 79-128
  - Exact passage: “مدة الاحتفاظ المعتمدة لسجلات الخدمة هي سبع سنوات.”
  - Passage SHA-256: `9b015ae1b38894ab89f3064077779b45581a9e84098a2e7b16b7cdf704995d74`
  - Claims: `ar-conflict-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-conflict-02

- Language: `ar`
- Question: أي فريق مسؤول عن الاستجابة للحوادث؟
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-ar-conflict-owner-v1` — ميثاق الاستجابة للحوادث; `fixtures/ar-conflict-owner.docx`; version `1.0`; SHA-256 `6cc747255d41f8aa32cbaedb339d3b85ddca66593bee4dcc5cab5eea2c515a19`
- `src-ar-conflict-owner-counter-v1` — ميثاق الاستجابة للحوادث - الحوكمة; `fixtures/ar-conflict-owner-counter.docx`; version `1.0`; SHA-256 `42b537a3009d328c3a60bceec9109b189e271306fc80118257fea92dee63566e`

Proposed atomic claims:

- `ar-conflict-02-claim-1` (`conflicted`): يسند أحد المصدرين المعتمدين المسؤولية إلى فريق العمليات الأمنية.

Proposed evidence anchors:

- `ar-conflict-02-ev-conflict-a` — source `src-ar-conflict-owner-v1`, role `conflicting`, heading السجل المعتمد, paragraph 3, characters 0-54
  - Exact passage: “يتولى فريق العمليات الأمنية مسؤولية الاستجابة للحوادث.”
  - Passage SHA-256: `bd8322d5b1618ce8aab1b8597bca758f541c5548acf433beeb40e270654a54ca`
  - Claims: `ar-conflict-02-claim-1`
- `ar-conflict-02-ev-conflict-b` — source `src-ar-conflict-owner-counter-v1`, role `conflicting`, heading السجل المعتمد, paragraph 3, characters 0-51
  - Exact passage: “يتولى فريق مرونة التقنية مسؤولية الاستجابة للحوادث.”
  - Passage SHA-256: `ddcf5b75cccfeda8264d644564783db191172a6fc35f973e15f75d4b9d813582`
  - Claims: `ar-conflict-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-conflict-03

- Language: `ar`
- Question: متى تدخل السياسة حيز التنفيذ؟
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-ar-conflict-date-v1` — إشعار بدء سريان السياسة; `fixtures/ar-conflict-date.pdf`; version `1.0`; SHA-256 `621bf4425295cd0b0f08b8f1f43b43aa4308b9ef991f336d317c91ccdbb4a752`
- `src-ar-conflict-date-counter-v1` — إشعار بدء سريان السياسة - الحوكمة; `fixtures/ar-conflict-date-counter.pdf`; version `1.0`; SHA-256 `f1d9a32f7e67a9d54f6614d569208db8e25462d8aaea38289a1a26a9d7c9bbbc`

Proposed atomic claims:

- `ar-conflict-03-claim-1` (`conflicted`): يذكر أحد المصدرين المعتمدين تاريخ الأول من يناير عام ألفين وستة وعشرين.

Proposed evidence anchors:

- `ar-conflict-03-ev-conflict-a` — source `src-ar-conflict-date-v1`, role `conflicting`, page 1, characters 68-133
  - Exact passage: “تدخل السياسة حيز التنفيذ في الأول من يناير عام ألفين وستة وعشرين.”
  - Passage SHA-256: `ae864e7ddc0efe44ad53b3dfc00ab10f46e7e976d70d836b61978bf923b4e73b`
  - Claims: `ar-conflict-03-claim-1`
- `ar-conflict-03-ev-conflict-b` — source `src-ar-conflict-date-counter-v1`, role `conflicting`, page 1, characters 78-142
  - Exact passage: “تدخل السياسة حيز التنفيذ في الأول من مارس عام ألفين وستة وعشرين.”
  - Passage SHA-256: `f7d417feaca9c32d491a71f04ecbcbad69a0f1d14f877b141e24b816e10f34a2`
  - Claims: `ar-conflict-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-conflict-04

- Language: `ar`
- Question: ما حجم العينة المذكور؟
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-ar-conflict-sample-v1` — مذكرة منهجية أخذ العينات; `fixtures/ar-conflict-sample.docx`; version `1.0`; SHA-256 `81d932da9e79a17d379d73bbe61dad86860a15ee879b7eade374e8303a52bc9a`
- `src-ar-conflict-sample-counter-v1` — مذكرة منهجية أخذ العينات - الحوكمة; `fixtures/ar-conflict-sample-counter.docx`; version `1.0`; SHA-256 `eb8e924d73b3a1d19435142a8944659bdd8f51a5dfceacbb58416be49ffd1c57`

Proposed atomic claims:

- `ar-conflict-04-claim-1` (`conflicted`): يذكر أحد المصدرين المعتمدين أن حجم العينة أربعمئة وثمانون.

Proposed evidence anchors:

- `ar-conflict-04-ev-conflict-a` — source `src-ar-conflict-sample-v1`, role `conflicting`, heading السجل المعتمد, paragraph 3, characters 0-55
  - Exact passage: “تتكون العينة المذكورة من أربعمئة وثمانين ملاحظة مكتملة.”
  - Passage SHA-256: `a03139a13564ad72b96879e1ae364573d3cd2aa6900110561920af9d37095102`
  - Claims: `ar-conflict-04-claim-1`
- `ar-conflict-04-ev-conflict-b` — source `src-ar-conflict-sample-counter-v1`, role `conflicting`, heading السجل المعتمد, paragraph 3, characters 0-58
  - Exact passage: “تتكون العينة المذكورة من خمسمئة واثنتي عشرة ملاحظة مكتملة.”
  - Passage SHA-256: `905cb193403c77c177f9db41eab8e0791af31df598fcf3800df3446b9f18a0eb`
  - Claims: `ar-conflict-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-conflict-05

- Language: `ar`
- Question: هل الضابط إلزامي؟
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-ar-conflict-control-v1` — معيار ضابط الأجهزة الطرفية; `fixtures/ar-conflict-control.pdf`; version `1.0`; SHA-256 `1efa69118a6e0aed6ef1d24130c9dbe453bbfd454b317442063e4afdfccf168f`
- `src-ar-conflict-control-counter-v1` — معيار ضابط الأجهزة الطرفية - الحوكمة; `fixtures/ar-conflict-control-counter.pdf`; version `1.0`; SHA-256 `a440ef63eebc38eba6cacb8029392f2ccac40cc0c6890cdc4fd79bf1a6819d8a`

Proposed atomic claims:

- `ar-conflict-05-claim-1` (`conflicted`): ينص أحد المصدرين المعتمدين على أن الضابط إلزامي.

Proposed evidence anchors:

- `ar-conflict-05-ev-conflict-a` — source `src-ar-conflict-control-v1`, role `conflicting`, page 1, characters 71-136
  - Exact passage: “ضابط عزل الأجهزة الطرفية إلزامي لجميع الحواسيب المحمولة المُدارة.”
  - Passage SHA-256: `42bc44d7d79b211b1139204464a6070de30c4da7476ce0c8e5be949ec76fb842`
  - Claims: `ar-conflict-05-claim-1`
- `ar-conflict-05-ev-conflict-b` — source `src-ar-conflict-control-counter-v1`, role `conflicting`, page 1, characters 81-157
  - Exact passage: “ضابط عزل الأجهزة الطرفية موصى به لكنه غير إلزامي للحواسيب المحمولة المُدارة.”
  - Passage SHA-256: `5945119499d8c75f3e76a5285bbdb17cae8c2ddd49bab3828c679671f6e8447a`
  - Claims: `ar-conflict-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-conflict-01

- Language: `en`
- Question: What is the approved retention period?
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-en-conflict-retention-v1` — Retention Schedule - Operations; `fixtures/en-conflict-retention.pdf`; version `1.0`; SHA-256 `c00450aa3418278d3b910a08dc07c47316fb3c3b4ff589ee885a6d9b77627ed9`
- `src-en-conflict-retention-counter-v1` — Retention Schedule - Operations - Governance; `fixtures/en-conflict-retention-counter.pdf`; version `1.0`; SHA-256 `db8a211bbfed62fe41abe79370d29d949e1e7413e44df8a08d9b25bfd7fe057b`

Proposed atomic claims:

- `en-conflict-01-claim-1` (`conflicted`): One verified source states five years.

Proposed evidence anchors:

- `en-conflict-01-ev-conflict-a` — source `src-en-conflict-retention-v1`, role `conflicting`, page 1, characters 91-155
  - Exact passage: “The approved retention period for service records is five years.”
  - Passage SHA-256: `93a30900ff4d1f698e74ab9c3d423e8e35818ccd7391861f535bc23eb0e40977`
  - Claims: `en-conflict-01-claim-1`
- `en-conflict-01-ev-conflict-b` — source `src-en-conflict-retention-counter-v1`, role `conflicting`, page 1, characters 104-169
  - Exact passage: “The approved retention period for service records is seven years.”
  - Passage SHA-256: `6d77b94315435182b7e616a22716b97f0b8d742a541769245996c00784a12cfd`
  - Claims: `en-conflict-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-conflict-02

- Language: `en`
- Question: Which team owns incident response?
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-en-conflict-owner-v1` — Incident Response Charter; `fixtures/en-conflict-owner.docx`; version `1.0`; SHA-256 `2ccdc171a960d10bd3cc4ab18ca57d5bdc47e689c1c8c6018ccfe2169a601769`
- `src-en-conflict-owner-counter-v1` — Incident Response Charter - Governance; `fixtures/en-conflict-owner-counter.docx`; version `1.0`; SHA-256 `8fa65764aba49adfede167db0489b9d74f05d4c500e6a7a2d469b44fa4c50dc4`

Proposed atomic claims:

- `en-conflict-02-claim-1` (`conflicted`): One verified source assigns ownership to Security Operations.

Proposed evidence anchors:

- `en-conflict-02-ev-conflict-a` — source `src-en-conflict-owner-v1`, role `conflicting`, heading Approved record, paragraph 3, characters 0-52
  - Exact passage: “The Security Operations team owns incident response.”
  - Passage SHA-256: `3026ec3a510ce8a172c8798c53f8cddf0cbfcc4e9cd24c9f9117f42a1b10ef75`
  - Claims: `en-conflict-02-claim-1`
- `en-conflict-02-ev-conflict-b` — source `src-en-conflict-owner-counter-v1`, role `conflicting`, heading Approved record, paragraph 3, characters 0-54
  - Exact passage: “The Technology Resilience team owns incident response.”
  - Passage SHA-256: `9ac7e1d4f781b5e5bbfeaa2fbe516142281553b4d3dd7fa594a50680384ec31e`
  - Claims: `en-conflict-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-conflict-03

- Language: `en`
- Question: When does the policy take effect?
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-en-conflict-date-v1` — Policy Commencement Notice; `fixtures/en-conflict-date.pdf`; version `1.0`; SHA-256 `63a9e2a378761b255acbe763b0fdf620b20c75723731af60d6fb78e4a346d704`
- `src-en-conflict-date-counter-v1` — Policy Commencement Notice - Governance; `fixtures/en-conflict-date-counter.pdf`; version `1.0`; SHA-256 `b79661feab4b896645f67aec1a3b72d6e6b7b2212bc6bccfa52014c4668e3da1`

Proposed atomic claims:

- `en-conflict-03-claim-1` (`conflicted`): One verified source gives 1 January 2026.

Proposed evidence anchors:

- `en-conflict-03-ev-conflict-a` — source `src-en-conflict-date-v1`, role `conflicting`, page 1, characters 86-128
  - Exact passage: “The policy takes effect on 1 January 2026.”
  - Passage SHA-256: `43a3b5044b973ffb075731bc58086a6a4a3f38a905f4f979932f8862749355de`
  - Claims: `en-conflict-03-claim-1`
- `en-conflict-03-ev-conflict-b` — source `src-en-conflict-date-counter-v1`, role `conflicting`, page 1, characters 99-139
  - Exact passage: “The policy takes effect on 1 March 2026.”
  - Passage SHA-256: `5f991d7a249d13a2f3f619f326213b6ba9e816b1ee7ae04fd64bcd2c29ddfc1b`
  - Claims: `en-conflict-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-conflict-04

- Language: `en`
- Question: What is the reported sample size?
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-en-conflict-sample-v1` — Sampling Method Note; `fixtures/en-conflict-sample.docx`; version `1.0`; SHA-256 `b8fcd91b1ec5575a75660dfa3d05326e31059a9b4a2a8e3061077157689405bb`
- `src-en-conflict-sample-counter-v1` — Sampling Method Note - Governance; `fixtures/en-conflict-sample-counter.docx`; version `1.0`; SHA-256 `a418ff5a5a4431863084320e7576ba062b3293a794cc06d4bdbf49a0fc86974e`

Proposed atomic claims:

- `en-conflict-04-claim-1` (`conflicted`): One verified source reports a sample size of 480.

Proposed evidence anchors:

- `en-conflict-04-ev-conflict-a` — source `src-en-conflict-sample-v1`, role `conflicting`, heading Approved record, paragraph 3, characters 0-56
  - Exact passage: “The reported sample contains 480 completed observations.”
  - Passage SHA-256: `61bb0d6b212f721dba18ded80e65e75871561d8ddb1b57864625d04ab31df27f`
  - Claims: `en-conflict-04-claim-1`
- `en-conflict-04-ev-conflict-b` — source `src-en-conflict-sample-counter-v1`, role `conflicting`, heading Approved record, paragraph 3, characters 0-56
  - Exact passage: “The reported sample contains 512 completed observations.”
  - Passage SHA-256: `3761b487b32595f726ca2720e162a47ab5945aa47f8f4fe9b476e4233d4117ee`
  - Claims: `en-conflict-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-conflict-05

- Language: `en`
- Question: Is the control mandatory?
- Proposed outcome: `CONTRADICTORY`
- Proposed correction required: `false`

Sources:

- `src-en-conflict-control-v1` — Endpoint Control Standard; `fixtures/en-conflict-control.pdf`; version `1.0`; SHA-256 `c5ff3fd5676a1e78c8b275d48acf6bdcd24fc313d557667808cbd6b365693589`
- `src-en-conflict-control-counter-v1` — Endpoint Control Standard - Governance; `fixtures/en-conflict-control-counter.pdf`; version `1.0`; SHA-256 `01b24fc8d8ad494ba29e78e6a02b5e0b5b72adb90db5c7e3f2aa1e72c704a9cd`

Proposed atomic claims:

- `en-conflict-05-claim-1` (`conflicted`): One verified source states that the control is mandatory.

Proposed evidence anchors:

- `en-conflict-05-ev-conflict-a` — source `src-en-conflict-control-v1`, role `conflicting`, page 1, characters 85-153
  - Exact passage: “The endpoint isolation control is mandatory for all managed laptops.”
  - Passage SHA-256: `f7a2cbf0f98e1718a6104b0be58445d900038a554152863dcd2657bdc8feea77`
  - Claims: `en-conflict-05-claim-1`
- `en-conflict-05-ev-conflict-b` — source `src-en-conflict-control-counter-v1`, role `conflicting`, page 1, characters 98-182
  - Exact passage: “The endpoint isolation control is recommended but not mandatory for managed laptops.”
  - Passage SHA-256: `e180d083a7efcdadb128c2409991de3430a6f56e246737dd4eede240596faf71`
  - Claims: `en-conflict-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:
