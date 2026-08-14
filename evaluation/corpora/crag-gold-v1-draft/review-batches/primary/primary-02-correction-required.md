# Primary review batch: primary-02-correction-required

Corpus: `crag-bilingual-gold` / `crag-gold-v1-draft`

This packet contains evaluator-only proposals. Inspect every source directly before deciding. Do not treat the proposal or any model assistance as approved truth.

## ar-correction-01

- Language: `ar`
- Question: ما الاستثناء الذي يغير القاعدة العامة؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: يستخدم السؤال تعبيراً عاماً أو قديماً؛ ويربطه دليل الجسر بالمصطلح المعتمد اللازم لاسترجاع المقطع المستهدف.

Sources:

- `src-ar-policy-b-v1` — دليل استثناءات المشتريات; `fixtures/ar-policy-b.pdf`; version `1.0`; SHA-256 `ef34963784cc0ab5ac7fec69f46f5cb3024ee15d60bf75860502bba7564848dc`

Proposed atomic claims:

- `ar-correction-01-claim-1` (`supported`): يسمح بند استمرارية الخدمة العاجلة بالشراء الفوري دون ثلاثة عروض عندما يهدد التأخير استمرارية الخدمة.

Proposed evidence anchors:

- `ar-correction-01-ev-bridge` — source `src-ar-policy-b-v1`, role `bridge`, page 1, characters 69-158
  - Exact passage: “يحمل استثناء الاستجابة للطوارئ الاسم الرسمي بند استمرارية الخدمة العاجلة ويُختصر إلى بسا.”
  - Passage SHA-256: `ed4193534fcdb01c32a918f75b46e3ed7e9b21e9d4df6017f2c65b15aa3d76f3`
  - Claims: `ar-correction-01-claim-1`
- `ar-correction-01-ev-target` — source `src-ar-policy-b-v1`, role `necessary`, page 6, characters 1572-1671
  - Exact passage: “بموجب بسا، يجوز لقائد الحادث اعتماد شراء فوري دون ثلاثة عروض إذا كان التأخير يهدد استمرارية الخدمة.”
  - Passage SHA-256: `7bf904263f14bdb84f21d985ae52d54d1a22db7a8e744ee76ea77ae444c15ddd`
  - Claims: `ar-correction-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-correction-02

- Language: `ar`
- Question: كيف يصف المصدر المصطلح القديم الآن؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: يستخدم السؤال تعبيراً عاماً أو قديماً؛ ويربطه دليل الجسر بالمصطلح المعتمد اللازم لاسترجاع المقطع المستهدف.

Sources:

- `src-ar-glossary-a-v1` — سجل مصطلحات السجلات; `fixtures/ar-glossary-a.docx`; version `1.0`; SHA-256 `1b64ebc5b3aae42669fbfb10e018ac52cee39e65f2fb2641eb6cd274e56c95b1`

Proposed atomic claims:

- `ar-correction-02-claim-1` (`supported`): أصبح المصطلح القديم الدفتر الأزرق يُسمى الآن سجل الحالات.

Proposed evidence anchors:

- `ar-correction-02-ev-bridge` — source `src-ar-glossary-a-v1`, role `bridge`, heading جسر المصطلحات, paragraph 3, characters 0-55
  - Exact passage: “يشير المصطلح القديم الدفتر الأزرق الآن إلى سجل الحالات.”
  - Passage SHA-256: `f5233d23ca1e1bad36a77bd31724a0d8b213303a90122b890acb2a949c7d2a7f`
  - Claims: `ar-correction-02-claim-1`
- `ar-correction-02-ev-target` — source `src-ar-glossary-a-v1`, role `necessary`, heading السجل المعتمد, paragraph 33, characters 0-61
  - Exact passage: “سجل الحالات هو السجل المعتمد حالياً للحالات الخدمية المفتوحة.”
  - Passage SHA-256: `c2697abf3986c6b49ddf56ac01543c99e60a75dd3d46f44e079828671678fad3`
  - Claims: `ar-correction-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-correction-03

- Language: `ar`
- Question: ما الدليل الذي يوضح الاختصار؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: يستخدم السؤال تعبيراً عاماً أو قديماً؛ ويربطه دليل الجسر بالمصطلح المعتمد اللازم لاسترجاع المقطع المستهدف.

Sources:

- `src-ar-technical-b-v1` — مواصفة النقل دون اتصال; `fixtures/ar-technical-b.pdf`; version `1.0`; SHA-256 `64366297350b32a16884900bdfd6f8ed514adcc1ff61d034184454c7bf0405e6`

Proposed atomic claims:

- `ar-correction-03-claim-1` (`supported`): يعني الاختصار ومغ وحدة المزامنة غير المتصلة التي تشفّر عمليات النقل المعلقة قبل التخزين المحلي.

Proposed evidence anchors:

- `ar-correction-03-ev-bridge` — source `src-ar-technical-b-v1`, role `bridge`, page 1, characters 67-131
  - Exact passage: “يرمز الاختصار ومغ في هذه المواصفة إلى وحدة المزامنة غير المتصلة.”
  - Passage SHA-256: `c4d770f604768f15f586e3e372100308ec519ad66c7a6fd5b0d6dce38bd726a2`
  - Claims: `ar-correction-03-claim-1`
- `ar-correction-03-ev-target` — source `src-ar-technical-b-v1`, role `necessary`, page 6, characters 1549-1620
  - Exact passage: “تُشفّر وحدة المزامنة غير المتصلة كل عملية نقل معلقة قبل التخزين المحلي.”
  - Passage SHA-256: `2ad4c3562bfb0888e2b6994d295ac6e2f92852a10198713c167322554a40b049`
  - Claims: `ar-correction-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-correction-04

- Language: `ar`
- Question: أي قسم يحتوي على الاسم التشغيلي؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: يستخدم السؤال تعبيراً عاماً أو قديماً؛ ويربطه دليل الجسر بالمصطلح المعتمد اللازم لاسترجاع المقطع المستهدف.

Sources:

- `src-ar-process-b-v1` — إجراء تشغيل استمرارية الأعمال; `fixtures/ar-process-b.docx`; version `1.0`; SHA-256 `68468372b3f0c8e5946eebbe634de49052b957115d7efaf539c50c8fd2016a7f`

Proposed atomic claims:

- `ar-correction-04-claim-1` (`supported`): يحتوي قسم عمليات التعافي على الاسم التشغيلي مكتب الاستمرارية.

Proposed evidence anchors:

- `ar-correction-04-ev-bridge` — source `src-ar-process-b-v1`, role `bridge`, heading جسر المصطلحات, paragraph 3, characters 0-48
  - Exact passage: “يتضمن قسم عمليات التعافي قواعد التسمية المعتمدة.”
  - Passage SHA-256: `c2959f2f83f1f61e961efb605d277fdce223bb8ac8e0d69fd5856469c3dfcac4`
  - Claims: `ar-correction-04-claim-1`
- `ar-correction-04-ev-target` — source `src-ar-process-b-v1`, role `necessary`, heading عمليات التعافي, paragraph 33, characters 0-57
  - Exact passage: “ضمن قسم عمليات التعافي تعمل الوحدة باسم مكتب الاستمرارية.”
  - Passage SHA-256: `ed6a4e7db5dd8b23b5121f9641dcefa7f03585a0fdda7247b526957efcd5686d`
  - Claims: `ar-correction-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## ar-correction-05

- Language: `ar`
- Question: ما المرادف الذي يحدد الضابط المطلوب؟
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: يستخدم السؤال تعبيراً عاماً أو قديماً؛ ويربطه دليل الجسر بالمصطلح المعتمد اللازم لاسترجاع المقطع المستهدف.

Sources:

- `src-ar-security-a-v1` — ضابط مفاتيح التشفير; `fixtures/ar-security-a.pdf`; version `1.0`; SHA-256 `0ad8cf88e2bc806bed628d7dd2e3e4deee49c320b4a1ee14bd8c8db9a7625438`

Proposed atomic claims:

- `ar-correction-05-claim-1` (`supported`): تحدد الحيازة المزدوجة ضابط الشخصين المطلوب لتصدير مفاتيح الإنتاج.

Proposed evidence anchors:

- `ar-correction-05-ev-bridge` — source `src-ar-security-a-v1`, role `bridge`, page 1, characters 64-120
  - Exact passage: “عبارة الحيازة المزدوجة هي المرادف المعتمد لضابط الشخصين.”
  - Passage SHA-256: `2981097ebb1222050f42ee060ddf4df6f8c0f82c73242073f241ee7eea038a21`
  - Claims: `ar-correction-05-claim-1`
- `ar-correction-05-ev-target` — source `src-ar-security-a-v1`, role `necessary`, page 6, characters 1557-1608
  - Exact passage: “يلزم ضابط الشخصين عند تصدير أي مفتاح تشفير للإنتاج.”
  - Passage SHA-256: `a06cecd82c93e6693f9c20da4b562e0da3b302da143cea6dab6edb355146ec11`
  - Claims: `ar-correction-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-correction-01

- Language: `en`
- Question: Which exception changes the general rule?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: The question uses a generic or legacy expression; the bridge maps it to the controlled term needed to retrieve the target passage.

Sources:

- `src-en-policy-b-v1` — Procurement Exceptions Manual; `fixtures/en-policy-b.pdf`; version `1.0`; SHA-256 `a4824c0538a6d48db7a1912b1be5f940fd5ecd073d013ca3cb8b9b34f91e4c86`

Proposed atomic claims:

- `en-correction-01-claim-1` (`supported`): The Rapid Continuity Clause permits an immediate purchase without three bids when delay threatens continuity.

Proposed evidence anchors:

- `en-correction-01-ev-bridge` — source `src-en-policy-b-v1`, role `bridge`, page 1, characters 92-178
  - Exact passage: “The emergency-response exception is formally titled the Rapid Continuity Clause (RCC).”
  - Passage SHA-256: `123fd562d17f768bdf9d6962e6dd87a34e79050ecd029481760fec036101866b`
  - Claims: `en-correction-01-claim-1`
- `en-correction-01-ev-target` — source `src-en-policy-b-v1`, role `necessary`, page 9, characters 768-900
  - Exact passage: “Under the RCC, an incident commander may authorize an immediate purchase without three bids when delay threatens service continuity.”
  - Passage SHA-256: `e43e3365ef5da5f92d0835f97df581a1512362ecadb22bd67378f7d061b11c99`
  - Claims: `en-correction-01-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-correction-02

- Language: `en`
- Question: How is the older term described now?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: The question uses a generic or legacy expression; the bridge maps it to the controlled term needed to retrieve the target passage.

Sources:

- `src-en-glossary-a-v1` — Records Terminology Register; `fixtures/en-glossary-a.docx`; version `1.0`; SHA-256 `319ae6fd64918903753c9d5597f15457ef07c46c23bde340e1c5231f0b463f9b`

Proposed atomic claims:

- `en-correction-02-claim-1` (`supported`): The older term Blue Ledger is now called the Case Register.

Proposed evidence anchors:

- `en-correction-02-ev-bridge` — source `src-en-glossary-a-v1`, role `bridge`, heading Terminology bridge, paragraph 3, characters 0-60
  - Exact passage: “The former term Blue Ledger now refers to the Case Register.”
  - Passage SHA-256: `4d5c58cdbb533d09c76436e77eab2d0209844bb3e9a3d621064e0fb4a0fc158e`
  - Claims: `en-correction-02-claim-1`
- `en-correction-02-ev-target` — source `src-en-glossary-a-v1`, role `necessary`, heading Approved record, paragraph 33, characters 0-74
  - Exact passage: “The Case Register is the current controlled record for open service cases.”
  - Passage SHA-256: `d3c118e64fd18f91424ee27d88c17ffef4967955cb16e65eb482923d8878c919`
  - Claims: `en-correction-02-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-correction-03

- Language: `en`
- Question: What evidence resolves the acronym?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: The question uses a generic or legacy expression; the bridge maps it to the controlled term needed to retrieve the target passage.

Sources:

- `src-en-technical-b-v1` — Offline Transfer Specification; `fixtures/en-technical-b.pdf`; version `1.0`; SHA-256 `e8e14be97c46f663e3fd482c226d7e0b8f5267907bec6d424208b7354a4d50db`

Proposed atomic claims:

- `en-correction-03-claim-1` (`supported`): OSM means Offline Sync Module, which encrypts queued transfers before local storage.

Proposed evidence anchors:

- `en-correction-03-ev-bridge` — source `src-en-technical-b-v1`, role `bridge`, page 1, characters 93-151
  - Exact passage: “In this specification, OSM expands to Offline Sync Module.”
  - Passage SHA-256: `4b1ed8c8f7df4df48d1196cf8cdcf6baaac8064290ebf62b5e73099003aa614e`
  - Claims: `en-correction-03-claim-1`
- `en-correction-03-ev-target` — source `src-en-technical-b-v1`, role `necessary`, page 9, characters 0-76
  - Exact passage: “The Offline Sync Module encrypts every queued transfer before local storage.”
  - Passage SHA-256: `4b4192717865768989fc33b1c08f18ae4d2fbc2dbd9ff24566735774669b7dda`
  - Claims: `en-correction-03-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-correction-04

- Language: `en`
- Question: Which section contains the operational name?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: The question uses a generic or legacy expression; the bridge maps it to the controlled term needed to retrieve the target passage.

Sources:

- `src-en-process-b-v1` — Continuity Operating Procedure; `fixtures/en-process-b.docx`; version `1.0`; SHA-256 `34e5d84a420d365ce82de528d0ebae231cb303097824cbe14685e08008492396`

Proposed atomic claims:

- `en-correction-04-claim-1` (`supported`): The Recovery Operations section contains the operational name Continuity Desk.

Proposed evidence anchors:

- `en-correction-04-ev-bridge` — source `src-en-process-b-v1`, role `bridge`, heading Terminology bridge, paragraph 3, characters 0-69
  - Exact passage: “The Recovery Operations section contains the controlled naming rules.”
  - Passage SHA-256: `09d32999db549dd761e1f9fed47bd88f30854f368d942164ddcff2dfcb64ccaf`
  - Claims: `en-correction-04-claim-1`
- `en-correction-04-ev-target` — source `src-en-process-b-v1`, role `necessary`, heading Recovery Operations, paragraph 33, characters 0-77
  - Exact passage: “Within Recovery Operations, the unit operates under the name Continuity Desk.”
  - Passage SHA-256: `fe38bff3856b04d1d895f07c1b201705c993d7e6065e358409cafa8b9b53751b`
  - Claims: `en-correction-04-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:

## en-correction-05

- Language: `en`
- Question: What synonym identifies the required control?
- Proposed outcome: `SUPPORTED`
- Proposed correction required: `true`
- Correction rationale: The question uses a generic or legacy expression; the bridge maps it to the controlled term needed to retrieve the target passage.

Sources:

- `src-en-security-a-v1` — Cryptographic Key Control; `fixtures/en-security-a.pdf`; version `1.0`; SHA-256 `af6e6367f47406b86c8467e60cdfc8132af4b9825f1da74676d5fd12ab13d7f2`

Proposed atomic claims:

- `en-correction-05-claim-1` (`supported`): Dual custody identifies the required two-person control for production key export.

Proposed evidence anchors:

- `en-correction-05-ev-bridge` — source `src-en-security-a-v1`, role `bridge`, page 1, characters 88-159
  - Exact passage: “The phrase dual custody is the approved synonym for two-person control.”
  - Passage SHA-256: `26c6fe6e8301387f43d704a48f3705b852d961e80aa725d4e45ecc12c7b221ea`
  - Claims: `en-correction-05-claim-1`
- `en-correction-05-ev-target` — source `src-en-security-a-v1`, role `necessary`, page 9, characters 0-80
  - Exact passage: “Two-person control is required whenever a production encryption key is exported.”
  - Passage SHA-256: `c8380ed5413105c6d0f9af0582003e86c5c418af271552f5789a9c898b8539d9`
  - Claims: `en-correction-05-claim-1`

Reviewer decision (complete the companion JSONL record):

- Decision: `approved` / `changes_required` / `adjudication_required`
- Reviewed outcome: `SUPPORTED` / `PARTIAL` / `INSUFFICIENT` / `CONTRADICTORY`
- Reviewed correction required: `true` / `false`
- Approved anchor IDs:
- Confidence: `high` / `medium` / `low`
- Uncertainty:
- Notes:
