from __future__ import annotations

import hashlib
import io
import math
import re
import threading
import time
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from docx import Document as DocxDocument
from pypdf import PdfReader

from crag.database import Database
from crag.domain import Chunk, Document, DocumentStatus, SourceAnchor, utc_now


class IngestionError(ValueError):
    pass


class OcrRequired(IngestionError):
    pass


@dataclass(slots=True)
class ParsedBlock:
    text: str
    anchor: SourceAnchor


def validate_upload(filename: str, content: bytes, max_bytes: int) -> tuple[str, str]:
    if not content:
        raise IngestionError("The uploaded file is empty.")
    if len(content) > max_bytes:
        raise IngestionError(f"File exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" and content.startswith(b"%PDF-"):
        return "application/pdf", suffix
    if suffix == ".docx" and content.startswith(b"PK"):
        _validate_docx_archive(content)
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", suffix
    raise IngestionError("Only valid PDF and DOCX files are supported.")


def _validate_docx_archive(content: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > 2_000:
                raise IngestionError("DOCX archive contains too many members.")
            expanded = sum(member.file_size for member in members)
            if expanded > 250 * 1024 * 1024:
                raise IngestionError("DOCX expands beyond the safe processing limit.")
            if "word/document.xml" not in {member.filename for member in members}:
                raise IngestionError("The file is not a valid DOCX document.")
    except zipfile.BadZipFile as exc:
        raise IngestionError("The DOCX archive is invalid.") from exc


def parse_document(path: Path, media_type: str, ocr_requested: bool) -> list[ParsedBlock]:
    if media_type == "application/pdf":
        blocks = _parse_pdf(path)
        text_chars = sum(len(block.text.strip()) for block in blocks)
        if text_chars < 40:
            if not ocr_requested:
                raise OcrRequired("This PDF appears image-only. Retry with optional OCR enabled.")
            return _parse_with_docling(path)
        return blocks
    return _parse_docx(path)


def _parse_pdf(path: Path) -> list[ParsedBlock]:
    try:
        reader = PdfReader(path)
        return [
            ParsedBlock(text=(page.extract_text() or "").strip(), anchor=SourceAnchor(page=index + 1))
            for index, page in enumerate(reader.pages)
            if (page.extract_text() or "").strip()
        ]
    except Exception as exc:
        raise IngestionError("PDF parsing failed. The file may be encrypted or damaged.") from exc


def _parse_docx(path: Path) -> list[ParsedBlock]:
    try:
        document = DocxDocument(path)
    except Exception as exc:
        raise IngestionError("DOCX parsing failed. The file may be damaged.") from exc
    heading_path: list[str] = []
    blocks: list[ParsedBlock] = []
    for index, paragraph in enumerate(document.paragraphs):
        text = paragraph.text.strip()
        if not text:
            continue
        style = paragraph.style.name if paragraph.style else ""
        match = re.match(r"Heading\s+(\d+)", style, re.IGNORECASE)
        if match:
            level = max(1, int(match.group(1)))
            heading_path = heading_path[: level - 1] + [text]
        blocks.append(
            ParsedBlock(
                text=text,
                anchor=SourceAnchor(
                    heading_path=heading_path.copy(),
                    paragraph_start=index,
                    paragraph_end=index,
                ),
            )
        )
    return blocks


def _parse_with_docling(path: Path) -> list[ParsedBlock]:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise IngestionError(
            "OCR was requested, but the optional Docling OCR dependency is not installed. "
            "Install the project's 'docling' extra and retry."
        ) from exc
    try:
        result = DocumentConverter().convert(path)
        text = result.document.export_to_markdown().strip()
    except Exception as exc:
        raise IngestionError("Local OCR could not extract usable text from this PDF.") from exc
    if len(text) < 40:
        raise IngestionError("OCR completed but found too little usable text.")
    return [ParsedBlock(text=text, anchor=SourceAnchor(page=1))]


def chunk_blocks(
    blocks: list[ParsedBlock],
    *,
    document_id: str,
    workspace_id: str,
    filename: str,
    target_chars: int = 1_200,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[ParsedBlock] = []
    current_size = 0

    def flush() -> None:
        nonlocal current, current_size
        if not current:
            return
        first, last = current[0], current[-1]
        anchor = first.anchor.model_copy(deep=True)
        anchor.paragraph_end = last.anchor.paragraph_end
        text = "\n\n".join(block.text for block in current).strip()
        chunks.append(
            Chunk(
                id=str(uuid4()), document_id=document_id, workspace_id=workspace_id,
                filename=filename, text=text, anchor=anchor, ordinal=len(chunks),
            )
        )
        current = []
        current_size = 0

    for block in blocks:
        if current and current_size + len(block.text) > target_chars:
            flush()
        if len(block.text) <= target_chars:
            current.append(block)
            current_size += len(block.text)
            continue
        for start in range(0, len(block.text), target_chars):
            part = block.text[start : start + target_chars]
            current.append(ParsedBlock(text=part, anchor=block.anchor))
            current_size = len(part)
            flush()
    flush()
    return chunks


class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str, *, is_query: bool = False) -> list[float]: ...

    def drain_telemetry(self) -> list[dict[str, object]]:
        return []


class HashingEmbedder(Embedder):
    """Offline deterministic baseline, not the production-quality embedding target."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed(self, text: str, *, is_query: bool = False) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.casefold(), re.UNICODE)
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "little")
            index = value % self.dimensions
            vector[index] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]


class OllamaEmbedder(Embedder):
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        keep_alive: str = "10m",
        timeout_seconds: float = 180.0,
        query_instruction: str | None = None,
        gpu_layers: int = -1,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.timeout_seconds = timeout_seconds
        self.query_instruction = query_instruction
        self.gpu_layers = gpu_layers
        self._telemetry: list[dict[str, object]] = []
        self._telemetry_lock = threading.Lock()

    def embed(self, text: str, *, is_query: bool = False) -> list[float]:
        model_input = (
            f"{self.query_instruction}\nQuery: {text}"
            if is_query and self.query_instruction
            else text
        )
        started = time.monotonic()
        payload: dict[str, object] = {}
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model,
                        "input": model_input,
                        "keep_alive": self.keep_alive,
                        "options": {"num_gpu": self.gpu_layers},
                    },
                )
                if response.is_error:
                    raise IngestionError(
                        f"Ollama embedding returned HTTP {response.status_code}: {response.text[:2000]}"
                    )
            payload = response.json()
        finally:
            record = {
                "operation": "query_embedding" if is_query else "document_embedding",
                "model": self.model,
                "wall_seconds": time.monotonic() - started,
                "total_duration_ns": payload.get("total_duration"),
                "load_duration_ns": payload.get("load_duration"),
                "prompt_eval_count": payload.get("prompt_eval_count"),
            }
            with self._telemetry_lock:
                self._telemetry.append(record)
        vectors = payload.get("embeddings", [])
        if not vectors:
            raise IngestionError(f"Ollama model '{self.model}' returned no embedding.")
        return [float(value) for value in vectors[0]]

    def drain_telemetry(self) -> list[dict[str, object]]:
        with self._telemetry_lock:
            records, self._telemetry = self._telemetry, []
        return records


class IngestionService:
    def __init__(
        self,
        database: Database,
        upload_dir: Path,
        max_upload_mb: int,
        embedder: Embedder | None = None,
    ):
        self.database = database
        self.upload_dir = upload_dir
        self.max_bytes = max_upload_mb * 1024 * 1024
        self.embedder = embedder or HashingEmbedder()
        upload_dir.mkdir(parents=True, exist_ok=True)

    def ingest(
        self,
        *,
        workspace_id: str,
        filename: str,
        content: bytes,
        ocr_requested: bool,
    ) -> Document:
        media_type, suffix = validate_upload(filename, content, self.max_bytes)
        digest = hashlib.sha256(content).hexdigest()
        duplicate = self.database.find_duplicate(workspace_id, digest)
        if duplicate:
            if ocr_requested and duplicate.status == DocumentStatus.NEEDS_OCR:
                storage_path = self.database.document_storage_path(duplicate.id)
                if not storage_path:
                    raise IngestionError("The stored scan could not be found for OCR retry.")
                self.database.prepare_ocr_retry(duplicate.id)
                return self._process(
                    self.database.get_document(duplicate.id), storage_path, media_type, True
                )
            return duplicate
        document_id = str(uuid4())
        storage_path = self.upload_dir / f"{document_id}{suffix}"
        storage_path.write_bytes(content)
        document = self.database.create_document(
            {
                "id": document_id, "workspace_id": workspace_id,
                "filename": Path(filename).name, "media_type": media_type,
                "sha256": digest, "status": DocumentStatus.PROCESSING,
                "ocr_requested": ocr_requested, "storage_path": str(storage_path),
                "created_at": utc_now(),
            }
        )
        return self._process(document, storage_path, media_type, ocr_requested)

    def _process(
        self,
        document: Document,
        storage_path: Path,
        media_type: str,
        ocr_requested: bool,
    ) -> Document:
        try:
            blocks = parse_document(storage_path, media_type, ocr_requested)
            chunks = chunk_blocks(
                blocks, document_id=document.id, workspace_id=document.workspace_id,
                filename=document.filename,
            )
            if not chunks:
                raise IngestionError("No usable text was found in the document.")
            self.database.replace_chunks(
                document.id, [(chunk, self.embedder.embed(chunk.text)) for chunk in chunks]
            )
            self.database.update_document_status(document.id, DocumentStatus.READY)
        except OcrRequired as exc:
            self.database.update_document_status(document.id, DocumentStatus.NEEDS_OCR, str(exc))
        except Exception as exc:
            self.database.update_document_status(document.id, DocumentStatus.FAILED, str(exc))
        return self.database.get_document(document.id)
