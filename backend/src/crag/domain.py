from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    NEEDS_OCR = "needs_ocr"
    FAILED = "failed"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationLabel(StrEnum):
    RELEVANT = "relevant"
    PARTIAL = "partially_relevant"
    IRRELEVANT = "irrelevant"


class VerificationLabel(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class Workspace(BaseModel):
    id: str
    name: str
    created_at: str


class Document(BaseModel):
    id: str
    workspace_id: str
    filename: str
    media_type: str
    sha256: str
    status: DocumentStatus
    ocr_requested: bool = False
    error: str | None = None
    created_at: str


class SourceAnchor(BaseModel):
    page: int | None = None
    heading_path: list[str] = Field(default_factory=list)
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    bounding_box: list[float] | None = None


class Chunk(BaseModel):
    id: str
    document_id: str
    workspace_id: str
    filename: str
    text: str
    anchor: SourceAnchor
    ordinal: int


class RetrievedChunk(Chunk):
    citation_id: str
    score: float


class QueryCreate(BaseModel):
    question: str = Field(min_length=2, max_length=4000)


class QueryRun(BaseModel):
    id: str
    workspace_id: str
    question: str
    status: RunStatus
    correction_count: int = 0
    rewritten_query: str | None = None
    result: AnswerResult | None = None
    error: str | None = None
    created_at: str
    updated_at: str


class ProgressEvent(BaseModel):
    id: int
    run_id: str
    kind: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class Citation(BaseModel):
    id: str
    document_id: str
    filename: str
    chunk_id: str
    passage: str
    anchor: SourceAnchor


class Claim(BaseModel):
    text: str
    citation_ids: list[str] = Field(min_length=1)


class Contradiction(BaseModel):
    summary: str
    citation_ids: list[str] = Field(min_length=2)


class AnswerResult(BaseModel):
    disposition: Literal["answered", "partial", "refused", "conflicting"]
    summary: str
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    refusal_reason: str | None = None


class RuntimeHealth(BaseModel):
    mode: str
    ready: bool
    detail: str


QueryRun.model_rebuild()

