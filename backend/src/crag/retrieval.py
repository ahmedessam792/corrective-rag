from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass

from crag.database import Database
from crag.domain import RetrievedChunk
from crag.ingestion import Embedder, HashingEmbedder


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False)) / (
        (math.sqrt(sum(a * a for a in left)) or 1.0)
        * (math.sqrt(sum(b * b for b in right)) or 1.0)
    )


class HybridRetriever:
    def __init__(self, database: Database, embedder: Embedder | None = None):
        self.database = database
        self.embedder = embedder or HashingEmbedder()

    def retrieve(self, workspace_id: str, query: str, limit: int = 12) -> list[RetrievedChunk]:
        return self.retrieve_with_trace(workspace_id, query, limit).results

    def retrieve_with_trace(self, workspace_id: str, query: str, limit: int = 12) -> RetrievalTrace:
        rows = self.database.chunk_rows(workspace_id)
        if not rows:
            return RetrievalTrace(query=query, results=[], dense_ranking=[], lexical_ranking=[], fused_ranking=[])
        query_vector = self.embedder.embed(query, is_query=True)
        dense = sorted(
            rows,
            key=lambda row: _cosine(query_vector, json.loads(row["vector_json"])),
            reverse=True,
        )[: max(limit * 2, 20)]
        tokens = [token for token in re.findall(r"\w+", query.casefold(), re.UNICODE) if len(token) > 1]
        fts_expression = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens[:12])
        lexical_ids = self.database.lexical_chunk_ids(workspace_id, fts_expression, max(limit * 2, 20))

        fused: dict[str, float] = {}
        for rank, row in enumerate(dense):
            fused[row["id"]] = fused.get(row["id"], 0.0) + 1 / (60 + rank)
        for rank, chunk_id in enumerate(lexical_ids):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1 / (60 + rank)
        by_id = {row["id"]: row for row in rows}
        ranked = sorted(fused, key=fused.get, reverse=True)[:limit]
        results = [
            RetrievedChunk(
                **self.database.row_to_chunk(by_id[chunk_id]).model_dump(),
                citation_id=f"E{index + 1}", score=fused[chunk_id],
            )
            for index, chunk_id in enumerate(ranked)
        ]
        return RetrievalTrace(
            query=query,
            results=results,
            dense_ranking=[row["id"] for row in dense],
            lexical_ranking=lexical_ids,
            fused_ranking=ranked,
        )


@dataclass(frozen=True, slots=True)
class RetrievalTrace:
    query: str
    results: list[RetrievedChunk]
    dense_ranking: list[str]
    lexical_ranking: list[str]
    fused_ranking: list[str]
