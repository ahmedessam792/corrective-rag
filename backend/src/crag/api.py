from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from crag.config import Settings, get_settings
from crag.database import Database
from crag.domain import (
    Document,
    QueryCreate,
    QueryRun,
    RunStatus,
    RuntimeHealth,
    Workspace,
    WorkspaceCreate,
)
from crag.ingestion import HashingEmbedder, IngestionError, IngestionService, OllamaEmbedder
from crag.retrieval import HybridRetriever
from crag.runtime import DeterministicRuntime, OllamaRuntime
from crag.workflow import CragWorkflow

TERMINAL = {RunStatus.COMPLETED, RunStatus.REFUSED, RunStatus.FAILED, RunStatus.CANCELLED}


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config.data_dir.mkdir(parents=True, exist_ok=True)
        database = Database(config.database_path)
        database.reconcile_incomplete_runs()
        runtime = (
            OllamaRuntime(
                config.ollama_url,
                config.chat_model,
                config.embed_model,
                context_size=config.ollama_context_size,
                output_tokens=config.ollama_output_tokens,
                seed=config.ollama_seed,
                gpu_layers=config.ollama_gpu_layers,
                keep_alive=config.ollama_keep_alive,
                timeout_seconds=config.ollama_timeout_seconds,
                repair_attempts=config.structured_repair_attempts,
            )
            if config.runtime == "ollama"
            else DeterministicRuntime()
        )
        embedder = (
            OllamaEmbedder(
                config.ollama_url,
                config.embed_model,
                keep_alive=config.ollama_keep_alive,
                timeout_seconds=config.ollama_timeout_seconds,
                gpu_layers=config.ollama_gpu_layers,
            )
            if config.runtime == "ollama"
            else HashingEmbedder()
        )
        app.state.settings = config
        app.state.database = database
        app.state.ingestion = IngestionService(
            database, config.upload_dir, config.max_upload_mb, embedder
        )
        app.state.workflow = CragWorkflow(
            database, HybridRetriever(database, embedder), runtime,
            max_corrections=config.max_corrections,
            context_chunks=config.context_chunks,
        )
        app.state.runtime = runtime
        yield
        database.close()

    app = FastAPI(
        title="Corrective RAG API",
        version="0.1.0",
        description="Local-only evidence retrieval, correction, verification, citation, and refusal.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    def database(request: Request) -> Database:
        return request.app.state.database

    @app.get("/api/health", response_model=RuntimeHealth)
    async def health(request: Request) -> RuntimeHealth:
        return await request.app.state.runtime.health()

    @app.get("/api/workspaces", response_model=list[Workspace])
    def list_workspaces(request: Request) -> list[Workspace]:
        return database(request).list_workspaces()

    @app.post("/api/workspaces", response_model=Workspace, status_code=status.HTTP_201_CREATED)
    def create_workspace(payload: WorkspaceCreate, request: Request) -> Workspace:
        return database(request).create_workspace(str(uuid4()), payload.name)

    @app.get("/api/workspaces/{workspace_id}", response_model=Workspace)
    def get_workspace(workspace_id: str, request: Request) -> Workspace:
        workspace = database(request).get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found.")
        return workspace

    @app.get("/api/workspaces/{workspace_id}/documents", response_model=list[Document])
    def list_documents(workspace_id: str, request: Request) -> list[Document]:
        if not database(request).get_workspace(workspace_id):
            raise HTTPException(status_code=404, detail="Workspace not found.")
        return database(request).list_documents(workspace_id)

    @app.post(
        "/api/workspaces/{workspace_id}/documents",
        response_model=Document,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_document(
        workspace_id: str,
        request: Request,
        file: UploadFile = File(...),
        ocr: bool = Form(False),
    ) -> Document:
        if not database(request).get_workspace(workspace_id):
            raise HTTPException(status_code=404, detail="Workspace not found.")
        content = await file.read(request.app.state.settings.max_upload_mb * 1024 * 1024 + 1)
        try:
            return await asyncio.to_thread(
                request.app.state.ingestion.ingest,
                workspace_id=workspace_id,
                filename=file.filename or "document",
                content=content,
                ocr_requested=ocr,
            )
        except IngestionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post(
        "/api/workspaces/{workspace_id}/queries",
        response_model=QueryRun,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def create_query(
        workspace_id: str,
        payload: QueryCreate,
        background_tasks: BackgroundTasks,
        request: Request,
    ) -> QueryRun:
        db = database(request)
        if not db.get_workspace(workspace_id):
            raise HTTPException(status_code=404, detail="Workspace not found.")
        if not any(document.status == "ready" for document in db.list_documents(workspace_id)):
            raise HTTPException(status_code=409, detail="Upload and index at least one source first.")
        run = db.create_run(str(uuid4()), workspace_id, payload.question)
        background_tasks.add_task(request.app.state.workflow.execute, run.id)
        return run

    @app.get("/api/runs/{run_id}", response_model=QueryRun)
    def get_run(run_id: str, request: Request) -> QueryRun:
        run = database(request).get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Query run not found.")
        return run

    @app.post("/api/runs/{run_id}/cancel", response_model=QueryRun)
    def cancel_run(run_id: str, request: Request) -> QueryRun:
        db = database(request)
        run = db.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Query run not found.")
        if run.status not in TERMINAL:
            db.request_cancel(run_id)
        return db.get_run(run_id)

    @app.get("/api/runs/{run_id}/events")
    async def stream_events(run_id: str, request: Request, after: int = 0) -> StreamingResponse:
        db = database(request)
        if not db.get_run(run_id):
            raise HTTPException(status_code=404, detail="Query run not found.")

        async def event_stream():
            cursor = after
            while True:
                if await request.is_disconnected():
                    break
                events = db.list_events(run_id, cursor)
                for event in events:
                    cursor = event.id
                    yield f"id: {event.id}\nevent: {event.kind}\ndata: {event.model_dump_json()}\n\n"
                run = db.get_run(run_id)
                if run and run.status in TERMINAL and not events:
                    yield f"event: done\ndata: {json.dumps({'run_id': run_id, 'status': run.status})}\n\n"
                    break
                await asyncio.sleep(0.2)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
