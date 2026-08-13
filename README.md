# Corrective RAG

A local-first evidence research application that retrieves, evaluates, corrects weak retrieval, verifies support, and either produces cited answers or refuses unsupported claims.

## Repository layout

- `backend/`: FastAPI API, ingestion, retrieval, CRAG orchestration, persistence, and evaluation.
- `frontend/`: React/Vite evidence workspace.
- `docs/`: canonical architecture, design, security, and tooling decisions.
- `evaluation/`: frozen bilingual fixture manifest and evaluation guidance.

## Quick start

Prerequisites: Python 3.12+, Node 20+, and optionally Ollama for real local inference.

```powershell
uv sync --extra dev
uv run uvicorn crag.api:app --app-dir backend/src --reload --port 8000
```

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The default `deterministic` model runtime is an offline development mode. It is deliberately conservative and is not the quality target. For real local inference, copy `.env.example` to `.env`, select `ollama`, install Ollama separately, and pull the configured models.

## Verification

```powershell
uv run pytest
uv run ruff check backend tests
Set-Location frontend
npm run typecheck
npm run test
npm run build
```

No production deployment, authentication, cloud fallback, or web search is included in this MVP.

The deterministic demo is not evidence of real-model quality. Use the paired local evaluation harness and acceptance procedure in [`docs/VALIDATION.md`](docs/VALIDATION.md) and [`evaluation/README.md`](evaluation/README.md).

Current measured status: **Validation failed / changes required**. See [`docs/VALIDATION_STATUS.md`](docs/VALIDATION_STATUS.md) for the exact runtime, hardware, correction, and evaluation blockers.
