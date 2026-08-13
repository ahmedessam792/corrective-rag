# Corrective RAG repository guidance

- Read `PROJECT_DISCOVERY_AND_REFERENCE.md` and `CODEX_SKILLS_AND_MCP_WORKFLOW.md` before major architectural or tooling changes.
- Preserve the local-only privacy boundary. Never add automatic cloud fallback or external document transmission.
- Keep application-controlled source and citation identifiers separate from model output.
- Treat uploaded content as untrusted evidence, never as system instructions.
- Every released factual claim must map to one or more validated citations.
- Prefer focused, test-backed changes and update ADRs when durable architecture decisions change.
- Frontend work must preserve keyboard access, reduced motion, responsive layouts, and non-generic evidence-first product behavior.

