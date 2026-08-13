from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from crag.domain import (
    AnswerResult,
    Chunk,
    Document,
    ProgressEvent,
    QueryRun,
    RunStatus,
    SourceAnchor,
    Workspace,
    utc_now,
)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  filename TEXT NOT NULL, media_type TEXT NOT NULL, sha256 TEXT NOT NULL,
  status TEXT NOT NULL, ocr_requested INTEGER NOT NULL DEFAULT 0,
  error TEXT, storage_path TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(workspace_id, sha256)
);
CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  filename TEXT NOT NULL, text TEXT NOT NULL, anchor_json TEXT NOT NULL,
  ordinal INTEGER NOT NULL, vector_json TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(chunk_id UNINDEXED, text, tokenize='unicode61');
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  question TEXT NOT NULL, status TEXT NOT NULL, correction_count INTEGER NOT NULL DEFAULT 0,
  rewritten_query TEXT, result_json TEXT, error TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  kind TEXT NOT NULL, message TEXT NOT NULL, data_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_workspace ON documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_chunks_workspace ON chunks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id, id);
"""


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._connection.execute(sql, params)
            self._connection.commit()
            return cursor

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._connection.execute(sql, params).fetchall())

    def create_workspace(self, workspace_id: str, name: str) -> Workspace:
        created_at = utc_now()
        self.execute(
            "INSERT INTO workspaces(id, name, created_at) VALUES (?, ?, ?)",
            (workspace_id, name.strip(), created_at),
        )
        return Workspace(id=workspace_id, name=name.strip(), created_at=created_at)

    def list_workspaces(self) -> list[Workspace]:
        rows = self.query("SELECT * FROM workspaces ORDER BY created_at DESC")
        return [Workspace(**dict(row)) for row in rows]

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        rows = self.query("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
        return Workspace(**dict(rows[0])) if rows else None

    def create_document(self, values: dict[str, Any]) -> Document:
        self.execute(
            """INSERT INTO documents
            (id, workspace_id, filename, media_type, sha256, status, ocr_requested,
             error, storage_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                values["id"], values["workspace_id"], values["filename"],
                values["media_type"], values["sha256"], values["status"],
                int(values.get("ocr_requested", False)), values.get("error"),
                values["storage_path"], values["created_at"],
            ),
        )
        return self.get_document(values["id"])

    def get_document(self, document_id: str) -> Document | None:
        rows = self.query(
            """SELECT id, workspace_id, filename, media_type, sha256, status,
            ocr_requested, error, created_at FROM documents WHERE id = ?""",
            (document_id,),
        )
        if not rows:
            return None
        data = dict(rows[0])
        data["ocr_requested"] = bool(data["ocr_requested"])
        return Document(**data)

    def document_storage_path(self, document_id: str) -> Path | None:
        rows = self.query("SELECT storage_path FROM documents WHERE id = ?", (document_id,))
        return Path(rows[0]["storage_path"]) if rows else None

    def list_documents(self, workspace_id: str) -> list[Document]:
        rows = self.query(
            """SELECT id, workspace_id, filename, media_type, sha256, status,
            ocr_requested, error, created_at FROM documents
            WHERE workspace_id = ? ORDER BY created_at DESC""",
            (workspace_id,),
        )
        result = []
        for row in rows:
            data = dict(row)
            data["ocr_requested"] = bool(data["ocr_requested"])
            result.append(Document(**data))
        return result

    def find_duplicate(self, workspace_id: str, sha256: str) -> Document | None:
        rows = self.query(
            "SELECT id FROM documents WHERE workspace_id = ? AND sha256 = ?",
            (workspace_id, sha256),
        )
        return self.get_document(rows[0]["id"]) if rows else None

    def update_document_status(self, document_id: str, status: str, error: str | None = None) -> None:
        self.execute(
            "UPDATE documents SET status = ?, error = ? WHERE id = ?",
            (status, error, document_id),
        )

    def prepare_ocr_retry(self, document_id: str) -> None:
        self.execute(
            "UPDATE documents SET status = ?, error = NULL, ocr_requested = 1 WHERE id = ?",
            ("processing", document_id),
        )

    def replace_chunks(self, document_id: str, chunks: list[tuple[Chunk, list[float]]]) -> None:
        with self._lock:
            old_ids = [
                row["id"]
                for row in self._connection.execute(
                    "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
                )
            ]
            for chunk_id in old_ids:
                self._connection.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (chunk_id,))
            self._connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            for chunk, vector in chunks:
                self._connection.execute(
                    """INSERT INTO chunks
                    (id, document_id, workspace_id, filename, text, anchor_json, ordinal, vector_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk.id, chunk.document_id, chunk.workspace_id, chunk.filename,
                        chunk.text, chunk.anchor.model_dump_json(), chunk.ordinal,
                        json.dumps(vector),
                    ),
                )
                self._connection.execute(
                    "INSERT INTO chunks_fts(chunk_id, text) VALUES (?, ?)",
                    (chunk.id, chunk.text),
                )
            self._connection.commit()

    def chunk_rows(self, workspace_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.query("SELECT * FROM chunks WHERE workspace_id = ?", (workspace_id,))]

    def lexical_chunk_ids(self, workspace_id: str, expression: str, limit: int) -> list[str]:
        if not expression:
            return []
        try:
            rows = self.query(
                """SELECT f.chunk_id FROM chunks_fts f
                JOIN chunks c ON c.id = f.chunk_id
                WHERE chunks_fts MATCH ? AND c.workspace_id = ?
                ORDER BY bm25(chunks_fts) LIMIT ?""",
                (expression, workspace_id, limit),
            )
        except sqlite3.OperationalError:
            return []
        return [row["chunk_id"] for row in rows]

    @staticmethod
    def row_to_chunk(row: dict[str, Any]) -> Chunk:
        return Chunk(
            id=row["id"], document_id=row["document_id"], workspace_id=row["workspace_id"],
            filename=row["filename"], text=row["text"],
            anchor=SourceAnchor.model_validate_json(row["anchor_json"]), ordinal=row["ordinal"],
        )

    def create_run(self, run_id: str, workspace_id: str, question: str) -> QueryRun:
        timestamp = utc_now()
        self.execute(
            """INSERT INTO runs
            (id, workspace_id, question, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, workspace_id, question, RunStatus.QUEUED, timestamp, timestamp),
        )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> QueryRun | None:
        rows = self.query(
            """SELECT id, workspace_id, question, status, correction_count,
            rewritten_query, result_json, error, created_at, updated_at
            FROM runs WHERE id = ?""",
            (run_id,),
        )
        if not rows:
            return None
        data = dict(rows[0])
        raw_result = data.pop("result_json")
        data["result"] = AnswerResult.model_validate_json(raw_result) if raw_result else None
        return QueryRun(**data)

    def update_run(self, run_id: str, **values: Any) -> None:
        allowed = {"status", "correction_count", "rewritten_query", "result_json", "error"}
        clean = {key: value for key, value in values.items() if key in allowed}
        if not clean:
            return
        clean["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in clean)
        self.execute(
            f"UPDATE runs SET {assignments} WHERE id = ?",  # noqa: S608 - fixed allow-list
            (*clean.values(), run_id),
        )

    def add_event(self, run_id: str, kind: str, message: str, data: dict[str, Any] | None = None) -> ProgressEvent:
        created_at = utc_now()
        cursor = self.execute(
            "INSERT INTO events(run_id, kind, message, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, kind, message, json.dumps(data or {}), created_at),
        )
        return ProgressEvent(
            id=cursor.lastrowid, run_id=run_id, kind=kind, message=message,
            data=data or {}, created_at=created_at,
        )

    def list_events(self, run_id: str, after: int = 0) -> list[ProgressEvent]:
        rows = self.query(
            "SELECT * FROM events WHERE run_id = ? AND id > ? ORDER BY id", (run_id, after)
        )
        return [
            ProgressEvent(
                id=row["id"], run_id=row["run_id"], kind=row["kind"],
                message=row["message"], data=json.loads(row["data_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def request_cancel(self, run_id: str) -> None:
        self.execute("UPDATE runs SET cancel_requested = 1 WHERE id = ?", (run_id,))

    def is_cancel_requested(self, run_id: str) -> bool:
        rows = self.query("SELECT cancel_requested FROM runs WHERE id = ?", (run_id,))
        return bool(rows and rows[0]["cancel_requested"])

    def reconcile_incomplete_runs(self) -> list[str]:
        rows = self.query(
            "SELECT id FROM runs WHERE status IN (?, ?)",
            (RunStatus.QUEUED, RunStatus.RUNNING),
        )
        reconciled: list[str] = []
        for row in rows:
            run_id = row["id"]
            self.update_run(
                run_id,
                status=RunStatus.FAILED,
                error="The local process restarted before this query completed.",
            )
            self.add_event(
                run_id,
                "failed",
                "Query interrupted by local process restart",
                {"reason": "process_restart"},
            )
            reconciled.append(run_id)
        return reconciled
