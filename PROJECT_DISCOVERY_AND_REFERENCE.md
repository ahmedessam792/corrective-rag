# PROJECT_DISCOVERY_AND_REFERENCE

> **Project:** Corrective RAG System (CRAG)  
> **Purpose of this document:** A consolidated discovery/reference document for future Codex planning.  
> **Status:** Research and discovery only. No implementation decisions in this document are final unless explicitly listed under **Confirmed Requirements**.  
> **Companion file:** `CODEX_SKILLS_AND_MCP_WORKFLOW.md`

---

## 1. Project Overview

### Purpose and value

The Corrective RAG System (CRAG) is a document-grounded question-answering system designed to improve on ordinary Retrieval-Augmented Generation (RAG).

Traditional RAG systems often retrieve context and immediately pass it to a language model, even when the retrieved chunks are weak, irrelevant, incomplete, or contradictory. CRAG adds an explicit corrective layer so the system can evaluate retrieval quality, repair poor retrieval, verify evidence, and refuse unsupported answers.

The main value proposition is:

**Retrieve → evaluate → correct when necessary → verify → answer only from trustworthy evidence.**

The system should be useful for research, internal knowledge, technical documentation, reports, policies, academic material, and other document-heavy workflows where traceability and groundedness matter.

### CRAG concept

The conceptual flow is:

1. User uploads one or more documents.
2. Documents are parsed, chunked, indexed, and prepared for retrieval.
3. User asks a question.
4. Initial retrieval returns candidate chunks.
5. The system evaluates retrieval relevance and quality.
6. If retrieval is weak or irrelevant:
   - the query is rewritten or refined,
   - retrieval runs again,
   - the new evidence is re-evaluated.
7. Candidate evidence is verified for actual answer support.
8. Only verified evidence is passed to answer generation.
9. The system returns:
   - a grounded answer with source references, or
   - an explicit insufficient-evidence/refusal response.

Important conceptual distinction:

- **Retrieval relevance:** Does this chunk relate to the question?
- **Answer support:** Does this evidence actually justify the answer?

A chunk may be relevant without being sufficient to support a claim.

### Target user experience

The intended user experience is closer to a **premium evidence-research workspace** than a conventional chatbot.

Users should be able to:

- upload and manage documents,
- ask questions naturally,
- inspect the evidence behind each answer,
- see when the system corrected weak retrieval,
- jump from a citation to the original document location,
- identify contradictory evidence,
- understand when the system cannot answer reliably.

The interface should expose useful workflow state without revealing private chain-of-thought reasoning.

### MVP scope

A realistic MVP should include:

- multi-document upload,
- document parsing and indexing,
- semantic retrieval,
- retrieval-quality evaluation,
- bounded query rewriting and re-retrieval,
- evidence verification,
- grounded answer generation,
- source citations,
- document/source inspection,
- explicit insufficient-evidence behavior,
- visible CRAG workflow progress,
- basic document management,
- clear loading, empty, processing, error, and unsupported-file states.

The MVP should avoid unnecessary expansion into:

- autonomous research agents,
- production deployment,
- web search,
- collaboration,
- complex analytics dashboards,
- multiple advanced retrieval pipelines before the core CRAG loop is validated.

### Local-only project constraint

The MVP will run **locally on the user's machine**.

There is currently **no production deployment requirement**.

### Free/local-model constraint

The project should prefer:

- local inference,
- open/free models,
- free-to-use options,
- zero or very low API cost,

while avoiding paid APIs where practical.

Cloud/free API use may be evaluated later, but local-first remains the current reference strategy.

---

## 2. Confirmed Requirements

The following are confirmed project requirements and should not be silently changed by Codex:

- [x] The product must be a proper web application with a separate frontend and backend.
- [x] Do **not** use Gradio.
- [x] Do **not** use Streamlit.
- [x] The MVP runs locally on the user's machine.
- [x] No production deployment is required for now.
- [x] Prefer free/local models and avoid paid APIs where practical.
- [x] Users can upload documents.
- [x] Users can ask questions about uploaded documents.
- [x] The system retrieves relevant chunks.
- [x] Retrieval quality must be evaluated before final answering.
- [x] Weak or irrelevant retrieval should trigger correction/query rewriting and re-retrieval.
- [x] The correction loop must be bounded.
- [x] Evidence must be verified before answer generation.
- [x] Final answers must be grounded only in verified context.
- [x] Answers must include source references/citations.
- [x] The system must explicitly handle questions that cannot be answered reliably.
- [x] Unsupported answers must be refused rather than hallucinated.
- [x] The frontend should feel elegant, premium, immersive, modern, visually compelling, and product-grade.
- [x] Avoid generic AI chatbot styling.
- [x] Avoid generic SaaS/dashboard structure and unnecessary dashboard pages.
- [x] Avoid stereotypical AI visual language such as random orange/purple gradients, excessive pills, generic card grids, excessive separators, and decorative AI effects.
- [x] `CODEX_SKILLS_AND_MCP_WORKFLOW.md` will exist in the project root.
- [x] Before major architecture, stack, design, or implementation decisions, Codex must inspect that workflow file and select only relevant expert-authored Skills/MCPs.
- [x] Codex must not treat the reference choices in this document as final decisions.

---

## 3. Reference Architecture

> **Important:** Everything in this section is a **reference recommendation, not a final decision**. Codex must independently validate these choices against the real repository, hardware, requirements, evaluation results, and the Skills/MCP workflow.

### Recommended architectural shape

Current reference direction:

**Modular monolith**

This is preferred over premature microservices for the MVP because it:

- keeps the system easier to reason about,
- reduces local operational complexity,
- still allows clear internal module boundaries,
- supports later extraction of workers/services if necessary.

### Frontend reference

**Next.js / React + TypeScript**

Reasoning:

- suitable for a polished application interface,
- good fit for adaptive research workspaces,
- supports streaming/progressive UX,
- compatible with the current frontend design direction.

This is not yet final.

### Backend reference

**Python + FastAPI**

Reasoning:

- strong Python ecosystem for document AI, retrieval, embeddings, evaluation, and local inference integration,
- suitable API layer for file uploads, streaming, and orchestration,
- keeps the backend independent from the frontend.

This is not yet final.

### CRAG orchestration

Three candidates remain open:

#### LangGraph

Current strongest reference candidate for explicit CRAG state transitions.

Potential states:

- retrieve,
- evaluate,
- rewrite,
- re-retrieve,
- verify,
- generate,
- refuse.

Strengths:

- explicit conditional workflow,
- state-machine style orchestration,
- good fit for bounded corrective loops.

#### Custom state machine

Potentially better if CRAG remains small and deterministic enough that a framework creates unnecessary abstraction.

Strengths:

- minimal dependencies,
- full control,
- straightforward debugging,
- explicit deterministic routing.

#### LlamaIndex Workflows

A realistic alternative if the project benefits from more RAG-specific abstractions and integrations.

Codex should compare all three rather than assuming one is correct.

### Document parsing

**Docling** is the current reference candidate.

Desired ingestion path:

**Upload → validate → parse → preserve metadata → chunk → embed → index**

Important metadata should survive ingestion:

- source/document ID,
- file name,
- page,
- section/heading,
- chunk ID,
- source offsets where possible.

Citation quality depends on metadata preservation.

### Vector storage

Two main reference candidates:

#### PostgreSQL + pgvector

Advantages:

- simple infrastructure,
- relational metadata and vector storage can coexist,
- attractive for an MVP that values operational simplicity.

#### Qdrant

Advantages:

- retrieval-focused capabilities,
- strong fit for hybrid retrieval and richer retrieval experimentation.

Codex must independently validate:

- local setup complexity,
- expected document scale,
- metadata needs,
- dense/hybrid retrieval plans,
- evaluation results.

### Retrieval and reranking

Reference retrieval progression:

**Initial retrieval → optional reranking → evaluator**

Possible design:

- dense semantic retrieval first,
- later hybrid dense + lexical retrieval if evaluation justifies it,
- metadata filters where useful,
- optional reranker before the LLM evaluator.

The reranker should not be confused with the CRAG evaluator.

### Evaluator vs verifier separation

These are intentionally separate concepts.

#### Retrieval evaluator

Question:

> Are the retrieved chunks relevant and good enough to continue?

Possible structured states:

- `relevant`
- `partially_relevant`
- `irrelevant`

#### Evidence verifier

Question:

> Does the candidate evidence actually support a reliable answer?

Possible structured states:

- `SUPPORTED`
- `PARTIAL`
- `INSUFFICIENT`
- `CONTRADICTORY`

This separation is a core conceptual part of the project.

### Deterministic vs LLM responsibilities

#### Prefer deterministic application logic for

- file validation,
- metadata handling,
- source IDs,
- chunk bookkeeping,
- retrieval execution,
- ranking/fusion mechanics,
- score/threshold application,
- workflow routing after structured model outputs,
- correction-loop limits,
- context/token limits,
- citation mapping,
- checking that citation IDs exist,
- access/security controls,
- failure handling,
- refusal policy enforcement,
- structured progress-event emission.

#### Use LLM/model judgment for

- semantic retrieval-quality grading,
- query rewriting,
- difficult evidence-support judgments,
- contradiction interpretation,
- grounded answer generation.

Core principle:

**The model may recommend a state; deterministic application code controls the workflow.**

### Structured CRAG progress events

The frontend should not see a frozen spinner during local inference.

The backend should expose semantic progress such as:

- `retrieval_started`
- `retrieval_completed`
- `reranking_started`
- `evaluation_started`
- `evaluation_weak`
- `query_rewritten`
- `retrieval_retry_started`
- `verification_started`
- `evidence_verified`
- `generation_started`
- `generation_completed`
- `insufficient_evidence`

Transport mechanism is still open.

### Local runtime separated from FastAPI

Current reference direction:

**FastAPI should not own the primary LLM lifecycle directly.**

Preferred shape:

```text
Frontend
   ↓
FastAPI
   ↓
CRAG Workflow
   ├─ Retrieval
   ├─ Embedding / reranking
   └─ ModelRuntime interface
          ↓
      Local inference runtime
```

Reasoning:

- avoid duplicate model loading during backend reloads,
- avoid multiple FastAPI workers each loading several GB of weights,
- allow runtime replacement without rewriting the application.

### Evaluation strategy

CRAG should be evaluated as a system, not only by individual model benchmarks.

The project should explicitly prove whether:

**CRAG > ordinary RAG**

on the project's own evaluation dataset.

---

## 4. Local Runtime & Free Models Reference

> **Reference only. These choices must be benchmarked on the actual machine before finalizing them.**

### Local-first strategy

Current preferred MVP strategy:

**Local by default + provider abstraction + cloud disabled by default**

Reasons:

- document privacy,
- no recurring API cost,
- no rate-limit dependency,
- predictable offline behavior,
- multiple CRAG calls per question do not consume external quotas.

Free cloud APIs may be used later for controlled benchmarking, but they should not become an automatic fallback for private documents.

### Current runtime reference: Ollama

**Ollama** is the current primary runtime reference for the local Windows MVP.

Reasons:

- easy local setup,
- Windows usability,
- quantized model support,
- localhost API,
- streaming,
- structured outputs,
- good integration with Python/FastAPI through HTTP.

### Runtime alternative: llama.cpp

**llama.cpp** is the strongest current alternative.

Reasons:

- more low-level control,
- GGUF support,
- CPU/GPU offloading,
- memory tuning,
- quantization flexibility,
- local HTTP server,
- grammar/schema-constrained output,
- useful benchmarking/control option.

### Other runtime roles

#### Hugging Face Transformers

Best treated as a research/evaluation option when:

- direct model control is required,
- embedding/reranking experimentation is needed,
- precision/quantization variants need to be benchmarked.

It is not currently the preferred main application runtime.

#### LM Studio

Potentially useful as a developer testing workbench.

#### vLLM

Relevant primarily if high GPU throughput or concurrent serving later becomes important.

It is not the primary reference for a simple local Windows MVP.

### Embedding model reference

**Qwen3-Embedding-0.6B**

Current reasons:

- small enough for local use,
- multilingual capability,
- suitable for retrieval,
- practical memory footprint,
- no need to begin with a much larger embedding model before evaluation justifies it.

### Optional reranker reference

**Qwen3-Reranker-0.6B**

Role:

**candidate chunks → reranker → stronger top evidence → CRAG evaluator**

This is optional.

Codex must validate whether reranking materially improves retrieval quality enough to justify additional runtime and memory complexity.

### Main CRAG model reference

**Qwen3.5 4B / 9B**

Reference responsibilities:

- retrieval evaluation,
- query rewriting,
- evidence verification,
- grounded answer generation.

Current reasoning:

One capable instruction model can likely handle several semantic CRAG stages more efficiently than loading multiple separate generative models.

Reference hierarchy:

- weaker/normal hardware → **Qwen3.5 4B**
- stronger hardware → **Qwen3.5 9B**
- significantly weaker hardware → smaller model only as a fallback, with verifier quality carefully evaluated.

### Hardware tiers

These are approximate reference tiers, not guarantees.

| Hardware | Reference main model | Notes |
|---|---|---|
| CPU-only / low-end machine | ~0.8B–2B Q4 fallback | May be slow and weaker for verification; keep contexts small |
| 16 GB RAM | Qwen3.5 4B Q4 | Current minimum practical target |
| 32 GB RAM | Qwen3.5 9B Q4 | Strong balanced CPU/local option |
| NVIDIA GPU ~6–8 GB VRAM | Qwen3.5 4B Q4 | Better responsiveness |
| NVIDIA GPU ~12 GB VRAM | Qwen3.5 9B Q4 | Strong MVP target |
| NVIDIA GPU ~16–24 GB VRAM | 9B at higher precision or larger benchmark candidates | More experimentation headroom |

Actual Codex planning must use the real machine specifications.

### Quantization strategy

Quantization makes sense for the local MVP.

Important distinction:

- **GGUF** is a model/container format commonly used by llama.cpp-style runtimes.
- **Q4/Q5/Q6/Q8** describe lower-precision weight representations.

Current reference:

- main generative LLM → **Q4_K_M** starting point,
- test **Q5_K_M** if memory allows and quality improvement is meaningful,
- embeddings → prefer Q8 or higher precision where practical,
- reranker → prefer Q8 or higher precision where practical.

The embedding/reranking models are small enough that aggressively quantizing them may provide less benefit than preserving retrieval quality.

### Context-window considerations

Do not select working context size from the model's advertised maximum.

For CRAG, retrieval should reduce context.

Current reference:

**8K–16K working context**

unless evaluation proves a larger window is necessary.

Larger context affects:

- RAM/VRAM,
- KV-cache size,
- latency,
- prompt processing time.

### Privacy

Local-first gives the project an important privacy property:

**Uploaded document content does not need to leave the machine.**

This claim is only valid if:

- external APIs are disabled,
- cloud fallback is disabled,
- telemetry/analytics do not send document content,
- external embedding services are not silently used.

### Prompt injection

Uploaded documents must be treated as untrusted data.

Requirements for later design:

- document text must never become system-level instructions,
- retrieved content must remain isolated as evidence,
- document instructions must not override trusted project policy,
- normal document QA should not grant arbitrary network/tool access to the answer model,
- source IDs and citation metadata must come from application-controlled metadata,
- sensitive document content should not be indiscriminately written to logs.

CRAG verification improves groundedness, but does not by itself solve prompt injection.

### No automatic cloud fallback

Current reference policy:

**Do not automatically send private document context to a free or paid external API when local inference fails.**

Any future external model usage should be explicit and opt-in.

---

## 5. Frontend Product Structure

> **Reference direction only. Codex may challenge or refine this after dedicated design planning.**

### Start / Library experience

Avoid a dashboard full of cards and metrics.

Reference structure:

```text
CRAG

What are you investigating?

[ Drop documents or open a workspace ]

Recent research
────────────────────────
Workspace A
Workspace B
Workspace C
```

The Start/Library screen should remain calm and task-oriented.

### Main adaptive workspace

Current core model:

**Sources → Research Canvas → Evidence Lens**

Reference layout:

```text
┌────────────┬──────────────────────────┬───────────────────┐
│ SOURCES    │     RESEARCH CANVAS      │   EVIDENCE LENS   │
│            │                          │                   │
│ report.pdf │ Question                 │ Source            │
│ paper.pdf  │ Answer                   │ Page / section    │
│ notes.docx │ Citations                │ Highlighted text  │
│            │ CRAG status              │ Context           │
└────────────┴──────────────────────────┴───────────────────┘
```

The interface should be adaptive rather than permanently fixed to three visible panels.

Examples:

- asking a question → Research Canvas becomes dominant,
- opening a citation → Evidence Lens becomes prominent,
- reading a source → document view expands,
- Sources can collapse to a narrow rail.

### Document interaction

Users should be able to:

- inspect uploaded sources,
- identify processing state,
- open a document,
- navigate to cited locations,
- inspect the surrounding source context,
- understand source/page/section metadata where available.

### Citation and evidence interaction

Citations should be first-class UI objects, not plain footnote numbers.

Desired behavior:

**claim → citation → Evidence Lens → exact supporting passage**

The user should remain in the research workspace rather than navigating away.

### Correction Trace

Visible, concise CRAG process information:

```text
Evidence trail

✓ Retrieved candidate passages
! Evidence quality was weak
↻ Search query refined
✓ Stronger passages retrieved
✓ Evidence verified
✓ Answer grounded
```

This shows observable workflow events, not private reasoning.

Collapsed form may show:

**Verified from 4 passages · 2 retrieval passes**

### Contradiction handling

If verified sources disagree, the interface should make the conflict explicit.

Example concept:

```text
Evidence conflict detected

Source A → supports claim X
Source B → supports claim Y
```

The system should not silently hide disagreement inside a confident answer.

### Evidence-aware refusal

A refusal should feel intentional rather than like an application error.

Reference concept:

```text
No reliable answer found

The available documents do not provide
enough verified evidence.

Related passages: 2
Sufficient supporting passages: 0

[Inspect nearest evidence]   [Choose more sources]
```

---

## 6. UI/UX & Visual Direction

> **All choices in this section are current references, not final design decisions. Codex should challenge them during the dedicated design stage.**

### Desired product character

The product should feel:

- elegant,
- premium,
- immersive,
- visually compelling,
- modern,
- trustworthy,
- research-oriented,
- like a real product entering the market.

### Avoid

- generic AI chatbot layouts,
- stereotypical SaaS dashboards,
- repetitive card grids,
- excessive bordered panels,
- random orange/purple AI gradients,
- excessive pills,
- decorative separators,
- glowing AI orbs,
- excessive glassmorphism,
- meaningless background animations,
- generic “AI startup” visuals.

### Current design-system reference

**shadcn/ui + Base UI foundation + custom CRAG design system**

Conceptually:

- Base UI → accessibility/interaction foundation,
- shadcn/ui → owned component composition/code layer,
- CRAG design system → actual visual identity.

Important:

Do not use the default shadcn look as the project's brand.

### Alternative design-system reference

**HeroUI v3**

Potential advantage:

- faster path to polished components,
- strong built-in component quality,
- modern interaction support.

Potential tradeoff:

- slightly less visual independence than building more deeply from a headless foundation.

### Other candidates previously considered

- Ark UI
- Base UI directly
- React Aria Components

These remain valid candidates if Codex concludes the final frontend architecture benefits from them.

### Visual style

Current reference concept:

**Dark editorial research environment + warm document surfaces**

The application chrome should feel dark, calm, mineral, and restrained.

Documents/evidence can use a warmer paper-like surface so evidence feels tangible and readable.

### Reference palette

| Purpose | Color |
|---|---|
| Main canvas | `#0B0F0E` |
| Primary surface | `#111714` |
| Elevated surface | `#18201D` |
| Hairlines | `#29332F` |
| Main text | `#F1F4F1` |
| Muted text | `#96A29C` |
| Document paper | `#F2EFE7` |
| Paper text | `#222622` |
| Verified | `#68D39B` |
| Retrieval | `#73B7E8` |
| Correction | `#D8B768` |
| Unsupported | `#DF7373` |

Semantic colors should be restrained.

Example:

- green → verified,
- blue → retrieval,
- amber → correction,
- muted red → unsupported/conflict.

### Typography reference

**Instrument Sans**

Primary use:

- product UI,
- navigation,
- headings,
- interface labels.

**Source Serif 4**

Primary use:

- document extracts,
- evidence,
- long-form reading,
- selected answer typography where appropriate.

Desired character:

**software × research publication**

### Spacing/layout character

Use:

- strong hierarchy,
- generous whitespace around primary tasks,
- higher density inside evidence/document views,
- alignment and surface tone rather than constant borders,
- minimal chrome around the main research task.

### Icon direction

Reference:

- ~18 px geometric line icons,
- ~1.5 px stroke,
- restrained,
- custom symbols where useful for:
  - Retrieve
  - Correct
  - Verify
  - Evidence

Avoid sparkles and magic-wand-heavy AI iconography.

### Motion direction

Motion should explain system state.

Good uses:

- workspace transitions,
- retrieval-stage progress,
- evidence appearance,
- citation-to-source transitions,
- document ingestion stages,
- subtle interface state changes.

Avoid animation for decoration alone.

Reference timing character:

- subtle,
- responsive,
- approximately 150–250 ms for ordinary interface transitions where appropriate.

### Inspiration principles

#### NotebookLM

Learn:

- adaptive source/chat/output workspace thinking,
- keeping sources closely connected to research,
- navigating from answers back into source material.

Do not copy Google's visual identity.

#### Perplexity

Learn:

- making citations first-class answer elements,
- keeping sources visible and inspectable.

#### Elicit

Learn:

- evidence-first research UX,
- making evidence auditable and comparable.

#### Linear

Learn:

- information hierarchy,
- restraint,
- dense professional interfaces where secondary chrome visually recedes.

#### Raycast

Learn:

- interaction polish,
- compactness,
- responsiveness,
- restrained depth and motion.

Do not copy these products directly; extract interaction/design principles only.

---

## 7. Standout Product Features

### Evidence Lens

A dedicated evidence surface opened from a citation.

Should show:

- source,
- page/section,
- highlighted evidence,
- surrounding context,
- source metadata.

### Correction Trace

Shows observable CRAG workflow state such as:

- initial retrieval,
- weak retrieval detection,
- query refinement,
- re-retrieval,
- evidence verification.

Should not expose hidden chain-of-thought reasoning.

### Claim-to-Evidence Highlighting

Hovering or selecting a factual claim in the answer should highlight the evidence supporting that specific claim.

Potential interaction:

**claim → supporting citation(s) → matching passages highlighted**

### Contradiction View

When sources disagree:

- show the conflicting claims,
- show which source supports each position,
- avoid silently synthesizing them into false certainty.

### Evidence-aware refusal

When evidence is insufficient:

- refuse explicitly,
- explain that the available sources are insufficient,
- optionally show nearest related evidence,
- offer a next useful user action.

### Visible CRAG workflow progress

Instead of a generic spinner:

```text
Searching documents
        ↓
Reranking
        ↓
Evaluating evidence
        ↓
Refining search
        ↓
Retrieving again
        ↓
Verifying
        ↓
Generating grounded answer
```

This is especially important for local models where latency may be noticeable.

---

## 8. Evaluation Strategy

The project should prove that CRAG improves over ordinary RAG rather than only implementing a CRAG-shaped workflow.

### Golden dataset

Build a representative evaluation dataset containing:

- straightforward answerable questions,
- misleading initial retrieval,
- questions requiring query correction,
- unanswerable questions,
- incomplete evidence,
- contradictory sources,
- potentially ambiguous questions,
- Arabic examples where relevant,
- English examples where relevant,
- mixed-language cases if expected in real usage.

### Retrieval evaluation

Measure metrics such as:

- Recall@K,
- MRR,
- nDCG,
- whether the true evidence is retrieved,
- whether reranking improves evidence ordering.

### Correction improvement

Measure retrieval before and after correction.

Key question:

> Does query rewriting/re-retrieval measurably improve retrieval quality?

### Grader / verifier evaluation

Use human-labelled examples.

Measure:

- precision,
- recall,
- macro-F1,
- confusion matrix,
- structured-output validity.

### False SUPPORTED cases

Treat this as a high-priority metric.

A dangerous failure is:

**Verifier says SUPPORTED when the evidence does not actually support the answer.**

Track this separately.

### Groundedness

Evaluate whether generated claims are supported by verified context.

Potential evaluation levels:

- answer-level groundedness,
- claim-level support,
- unsupported claim count.

### Citation correctness

Check:

- citation exists,
- cited source exists,
- cited page/section/chunk exists,
- passage actually supports the associated claim.

Citation validation should be deterministic where possible.

### Refusal accuracy

Measure:

- correct refusal when evidence is insufficient,
- incorrect refusal when evidence was actually sufficient,
- unsupported answer rate.

### Performance measurements

Record:

- cold-start latency,
- warm latency,
- time-to-first-token,
- total CRAG request latency,
- embedding latency,
- retrieval latency,
- reranking latency,
- grader latency,
- verifier latency,
- generation latency,
- peak RAM,
- peak VRAM,
- tokens/sec where relevant.

### Multilingual evaluation

If Arabic/English use is relevant, evaluate them separately.

Do not assume a model labelled “multilingual” performs equally well across:

- Arabic retrieval,
- Arabic evidence grading,
- Arabic query rewriting,
- Arabic generation,
- mixed Arabic/English documents.

---

## 9. Open Decisions for Codex

Codex must independently validate these later.

### Core stack

- [ ] Final frontend framework and frontend architecture.
- [ ] Final backend framework and backend architecture.
- [ ] Whether the modular-monolith reference remains appropriate.

### CRAG orchestration

- [ ] LangGraph vs custom workflow/state machine vs LlamaIndex Workflows.
- [ ] State representation and workflow boundaries.
- [ ] Retry/failure behavior.

### Retrieval/storage

- [ ] pgvector vs Qdrant.
- [ ] Dense-only vs hybrid retrieval.
- [ ] Lexical/BM25 role if hybrid retrieval is selected.
- [ ] Whether reranking materially improves the MVP.
- [ ] Retrieval candidate count and top-K values.
- [ ] Metadata-filter strategy.

### Documents/chunking

- [ ] Final parser.
- [ ] Whether Docling remains the best parser.
- [ ] Chunking strategy.
- [ ] Chunk size/overlap.
- [ ] Structure-aware chunking.
- [ ] Tables/images/scanned PDF handling.
- [ ] Metadata preservation requirements.
- [ ] Duplicate handling.

### Models

- [ ] Final embedding model.
- [ ] Final reranker model.
- [ ] Final evaluator model.
- [ ] Final query-rewriter model.
- [ ] Final verifier model.
- [ ] Final answer-generation model.
- [ ] Whether one instruction model should handle multiple CRAG stages.
- [ ] Whether Arabic/English quality is sufficient.

### Local runtime

- [ ] Ollama vs llama.cpp on the actual machine.
- [ ] Whether Transformers is needed for specialized model execution.
- [ ] Runtime/API abstraction design.
- [ ] 4B vs 9B main model.
- [ ] Actual model memory footprint.
- [ ] CPU/GPU placement.
- [ ] Model load/unload policy.
- [ ] Concurrency limits.
- [ ] Warm/cold model lifecycle.

### Quantization/context

- [ ] Q4_K_M vs Q5_K_M vs other practical quantization.
- [ ] Precision for embeddings.
- [ ] Precision for reranker.
- [ ] Actual working context window.
- [ ] KV-cache/memory impact.

### CRAG behavior

- [ ] Retrieval-quality thresholds.
- [ ] Evaluation labels.
- [ ] Evidence-verification labels.
- [ ] Correction-loop maximum.
- [ ] When correction should be skipped.
- [ ] Whether partially relevant evidence is retained.
- [ ] Contradiction policy.
- [ ] Partial-answer policy.
- [ ] Refusal policy details.

### Citation guarantees

- [ ] Citation granularity:
  - document,
  - page,
  - section,
  - chunk,
  - exact passage.
- [ ] Claim-to-citation mapping.
- [ ] Deterministic citation validation.
- [ ] Citation behavior for rewritten retrieval.
- [ ] Citation behavior for conflicting evidence.

### Streaming and progress

- [ ] SSE vs another transport for CRAG progress events.
- [ ] Token streaming strategy.
- [ ] Relationship between workflow events and answer streaming.
- [ ] Cancellation behavior.

### Hardware-dependent architecture

- [ ] Real CPU.
- [ ] Real RAM.
- [ ] Real GPU/VRAM if present.
- [ ] Whether architecture must change for the actual machine.
- [ ] Whether specialized models can remain resident simultaneously.
- [ ] Whether local runtime limits require tighter contexts or simpler retrieval.

### Frontend/design

- [ ] Final frontend product structure.
- [ ] Final design system.
- [ ] shadcn/ui + Base UI vs HeroUI v3 vs alternatives.
- [ ] Final typography.
- [ ] Final palette.
- [ ] Final light/dark behavior.
- [ ] Responsive/adaptive panel behavior.
- [ ] Final interaction/motion implementation.
- [ ] Evidence Lens implementation.
- [ ] Correction Trace implementation.
- [ ] Claim-to-Evidence highlighting behavior.
- [ ] Contradiction View behavior.
- [ ] Accessibility validation.

### Evaluation

- [ ] Golden dataset design.
- [ ] Normal RAG baseline.
- [ ] CRAG comparison methodology.
- [ ] Acceptance thresholds.
- [ ] False-SUPPORTED tolerance.
- [ ] Groundedness evaluation.
- [ ] Multilingual evaluation.
- [ ] Performance budgets.

---

## 10. Codex Skills/MCP Role

`CODEX_SKILLS_AND_MCP_WORKFLOW.md` is the project-level registry and routing policy that Codex must consult before major planning, architecture, frontend, stack, implementation, testing, or tooling decisions.

Before broad implementation, Codex should:

1. read the project brief and this discovery/reference file,
2. inspect the actual repository,
3. inspect the real machine/environment where relevant,
4. read applicable repository instructions such as `AGENTS.md`,
5. read `CODEX_SKILLS_AND_MCP_WORKFLOW.md`,
6. identify the exact task type,
7. select the **smallest useful set** of relevant expert-authored Skills/MCPs,
8. verify their original upstream sources and current compatibility,
9. reject or defer overlapping/unnecessary tools,
10. use the selected tools during planning and validation,
11. document durable tool-selection decisions before broad implementation.

Codex must **not** install every tool from the registry.

Codex must **not** create homemade replacements for existing expert-authored Skills/MCPs simply to force compatibility.

Likely future categories may include:

- engineering/planning Skill,
- architecture guidance,
- current documentation retrieval,
- stack-specific expert Skills,
- frontend/design-direction Skill,
- browser validation/testing,
- targeted design refinement.

The exact tools should only be selected after the repository and actual task are understood.

---

## 11. Final Reference Snapshot

### Product

**Corrective RAG System (CRAG)**

A local-first evidence research application that:

**retrieves → evaluates → corrects → re-retrieves → verifies → generates → cites or refuses.**

### Confirmed constraints

- proper frontend + backend web application,
- no Gradio,
- no Streamlit,
- local MVP,
- no production deployment now,
- free/local models preferred,
- evidence-grounded answers,
- correction loop,
- citations,
- explicit insufficient-evidence behavior,
- premium/non-generic frontend.

### Current architecture reference

```text
Next.js / React frontend
        ↓
FastAPI backend
        ↓
Explicit CRAG workflow
(LangGraph OR custom state machine OR LlamaIndex Workflows)
        ↓
Document ingestion / Docling
        ↓
Chunking + metadata
        ↓
Embeddings
        ↓
pgvector OR Qdrant
        ↓
Retrieval
        ↓
Optional reranker
        ↓
Retrieval evaluator
        ↓
Weak?
 ├─ No → Evidence verification
 └─ Yes → Query rewrite → Re-retrieve → Re-evaluate
        ↓
Evidence verification
 ├─ Supported → Grounded generation → Citation validation → Answer
 └─ Insufficient/unsupported → Refuse
```

### Local-model reference

```text
Embedding:
Qwen3-Embedding-0.6B

Optional reranker:
Qwen3-Reranker-0.6B

CRAG semantic stages:
Qwen3.5 4B or 9B

Runtime:
Ollama

Alternative runtime:
llama.cpp
```

No automatic cloud fallback.

### Hardware reference

- practical minimum → **16 GB RAM + Qwen3.5 4B Q4**
- balanced target → **32 GB RAM / or consumer NVIDIA GPU + Qwen3.5 9B Q4**
- weaker fallback → smaller model, smaller context, optional removal of reranker.

Actual hardware must be benchmarked.

### Frontend reference

```text
Start / Library

        ↓

Adaptive research workspace

Sources
   ↔
Research Canvas
   ↔
Evidence Lens
```

Core frontend ideas:

- Evidence Lens,
- Correction Trace,
- Claim-to-Evidence Highlighting,
- Contradiction View,
- evidence-aware refusal,
- visible CRAG workflow progress.

### Current visual reference

**Design system:** shadcn/ui + Base UI  
**Alternative:** HeroUI v3

**Style:** dark editorial research environment + warm document surfaces

**Palette:**

- `#0B0F0E` main canvas
- `#111714` primary surface
- `#18201D` elevated surface
- `#F1F4F1` text
- `#F2EFE7` document paper
- `#68D39B` verified
- `#73B7E8` retrieval
- `#D8B768` correction
- `#DF7373` unsupported

**Fonts:**

- Instrument Sans
- Source Serif 4

**Motion:** restrained and functional only.

### Product inspiration principles

- **NotebookLM** → adaptive source/research workspace
- **Perplexity** → citations as first-class answer elements
- **Elicit** → inspectable/auditable evidence
- **Linear** → hierarchy and restrained professional density
- **Raycast** → interaction polish and purposeful motion

### Primary success criterion

The project should not merely look like CRAG.

It should provide measurable evidence that:

> **The corrective workflow produces more reliable retrieval, grounded answers, citations, and refusals than a normal RAG baseline on the project's own evaluation dataset.**

### Status

All stack, architecture, runtime, model, vector database, retrieval, and visual-system choices above remain **reference recommendations only**.

Codex must independently validate them during the future planning phase using:

- the actual repository,
- the actual machine,
- this file,
- `CODEX_SKILLS_AND_MCP_WORKFLOW.md`,
- relevant expert-authored Skills/MCPs,
- project-specific evaluation evidence.

No implementation should be considered implied by this document.
