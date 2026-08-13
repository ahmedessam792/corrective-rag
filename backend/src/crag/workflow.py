from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from contextlib import suppress
from typing import TypeVar

from crag.database import Database
from crag.domain import (
    AnswerResult,
    Citation,
    Claim,
    EvaluationLabel,
    RetrievedChunk,
    RunStatus,
    VerificationLabel,
)
from crag.retrieval import HybridRetriever
from crag.runtime import ModelRuntime

T = TypeVar("T")


class Cancelled(Exception):
    pass


class CragWorkflow:
    def __init__(
        self,
        database: Database,
        retriever: HybridRetriever,
        runtime: ModelRuntime,
        *,
        max_corrections: int = 1,
        context_chunks: int = 6,
    ):
        self.database = database
        self.retriever = retriever
        self.runtime = runtime
        self.max_corrections = max_corrections
        self.context_chunks = context_chunks

    def emit(self, run_id: str, kind: str, message: str, **data: object) -> None:
        self.database.add_event(run_id, kind, message, data)

    def check_cancelled(self, run_id: str) -> None:
        if self.database.is_cancel_requested(run_id):
            raise Cancelled

    async def _await_stage(self, run_id: str, operation: Awaitable[T]) -> T:
        task = asyncio.create_task(operation)
        while not task.done():
            if self.database.is_cancel_requested(run_id):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
                raise Cancelled
            await asyncio.wait({task}, timeout=0.1)
        return await task

    def _emit_runtime_telemetry(self, run_id: str) -> None:
        for call in self.runtime.drain_telemetry():
            self.emit(run_id, "runtime_call_completed", "Local model call completed", **call.model_dump())

    def _emit_embedding_telemetry(self, run_id: str) -> None:
        for call in self.retriever.embedder.drain_telemetry():
            self.emit(run_id, "runtime_call_completed", "Local embedding call completed", **call)

    async def execute(self, run_id: str) -> None:
        run = self.database.get_run(run_id)
        if not run:
            return
        self.database.update_run(run_id, status=RunStatus.RUNNING)
        try:
            health = await self._await_stage(run_id, self.runtime.health())
            if not health.ready:
                raise RuntimeError(health.detail)
            query = run.question
            correction_count = 0
            evidence: list[RetrievedChunk] = []

            while True:
                self.check_cancelled(run_id)
                event_kind = "retrieval_started" if correction_count == 0 else "retrieval_retry_started"
                self.emit(run_id, event_kind, "Searching indexed sources", pass_number=correction_count + 1)
                trace = await self._await_stage(
                    run_id,
                    asyncio.to_thread(self.retriever.retrieve_with_trace, run.workspace_id, query, 12),
                )
                evidence = trace.results
                self._emit_embedding_telemetry(run_id)
                self.emit(
                    run_id, "retrieval_completed", f"Retrieved {len(evidence)} candidate passages",
                    candidate_count=len(evidence), pass_number=correction_count + 1,
                    query=query, dense_ranking=trace.dense_ranking,
                    lexical_ranking=trace.lexical_ranking, fused_ranking=trace.fused_ranking,
                )
                if not evidence:
                    result = self._refusal("No indexed passage is relevant to this question.")
                    self._finish(run_id, result, RunStatus.REFUSED)
                    return

                self.emit(run_id, "evaluation_started", "Evaluating retrieval quality")
                evaluation = await self._await_stage(run_id, self.runtime.evaluate(query, evidence))
                self._emit_runtime_telemetry(run_id)
                self.emit(
                    run_id, "evaluation_completed", "Retrieval evaluation completed",
                    label=evaluation.label,
                )
                should_correct = (
                    evaluation.label != EvaluationLabel.RELEVANT
                    and correction_count < self.max_corrections
                )
                if not should_correct:
                    break
                self.emit(run_id, "evaluation_weak", "Initial evidence was too weak")
                query = await self._await_stage(run_id, self.runtime.rewrite(run.question, evidence))
                self._emit_runtime_telemetry(run_id)
                correction_count += 1
                self.database.update_run(
                    run_id, correction_count=correction_count, rewritten_query=query,
                )
                self.emit(run_id, "query_rewritten", "Search query refined", correction_count=correction_count)

            self.check_cancelled(run_id)
            selected = evidence[: self.context_chunks]
            self.emit(run_id, "verification_started", "Checking whether evidence can support an answer")
            verification = await self._await_stage(run_id, self.runtime.verify(run.question, selected))
            self._emit_runtime_telemetry(run_id)
            self.emit(
                run_id, "evidence_verified", "Evidence support check completed",
                label=verification.label,
            )
            if verification.label == VerificationLabel.INSUFFICIENT:
                result = self._refusal("The available documents do not provide enough verified evidence.")
                self.emit(run_id, "insufficient_evidence", result.refusal_reason or "Insufficient evidence")
                self._finish(run_id, result, RunStatus.REFUSED)
                return

            if verification.label == VerificationLabel.CONFLICTING:
                contradiction = verification.contradiction
                allowed = {item.citation_id for item in selected}
                cited = set(contradiction.citation_ids) if contradiction else set()
                if not contradiction or len(cited) < 2 or not cited <= allowed:
                    result = self._refusal("Conflicting evidence was detected but could not be cited safely.")
                    self._finish(run_id, result, RunStatus.REFUSED)
                    return
                result = AnswerResult(
                    disposition="conflicting",
                    summary="The verified sources conflict; no factual claim was released.",
                    citations=self._citations_for_ids(cited, selected),
                    contradictions=[contradiction],
                )
                self.emit(
                    run_id, "generation_completed", "Verified evidence conflict ready",
                    claim_count=0, citation_count=len(result.citations),
                )
                self._finish(run_id, result, RunStatus.COMPLETED)
                return

            self.check_cancelled(run_id)
            self.emit(run_id, "generation_started", "Drafting supported, cited claims")
            draft = await self._await_stage(run_id, self.runtime.draft(run.question, selected))
            self._emit_runtime_telemetry(run_id)
            validated_claims = await self._validate_claims(run_id, draft.claims, selected)
            if not validated_claims:
                result = self._refusal("A draft was produced, but no claim passed citation support checks.")
                self.emit(run_id, "insufficient_evidence", result.refusal_reason or "No supported claims")
                self._finish(run_id, result, RunStatus.REFUSED)
                return

            citations = self._citations(validated_claims, selected)
            if verification.label == VerificationLabel.PARTIAL or len(validated_claims) < len(draft.claims):
                disposition = "partial"
                contradictions = []
            else:
                disposition = "answered"
                contradictions = []
            result = AnswerResult(
                disposition=disposition,
                summary=" ".join(claim.text for claim in validated_claims),
                claims=validated_claims,
                citations=citations,
                contradictions=contradictions,
            )
            self.emit(
                run_id, "generation_completed", "Grounded answer ready",
                claim_count=len(validated_claims), citation_count=len(citations),
            )
            self._finish(run_id, result, RunStatus.COMPLETED)
        except Cancelled:
            self._emit_runtime_telemetry(run_id)
            self._emit_embedding_telemetry(run_id)
            self.database.update_run(run_id, status=RunStatus.CANCELLED)
            self.emit(run_id, "cancelled", "Query cancelled")
        except Exception as exc:
            self._emit_runtime_telemetry(run_id)
            self._emit_embedding_telemetry(run_id)
            self.database.update_run(run_id, status=RunStatus.FAILED, error=str(exc))
            self.emit(run_id, "failed", "The query could not be completed", error=str(exc))

    async def _validate_claims(
        self,
        run_id: str,
        claims: list[Claim],
        evidence: list[RetrievedChunk],
    ) -> list[Claim]:
        by_id = {item.citation_id: item for item in evidence}
        accepted: list[Claim] = []
        for claim in claims:
            cited = [by_id[citation_id] for citation_id in claim.citation_ids if citation_id in by_id]
            if len(cited) != len(claim.citation_ids) or not cited:
                continue
            self.check_cancelled(run_id)
            support = await self._await_stage(run_id, self.runtime.verify(claim.text, cited))
            self._emit_runtime_telemetry(run_id)
            self.emit(
                run_id,
                "claim_verification_completed",
                "Draft claim support check completed",
                claim=claim.text,
                citation_ids=claim.citation_ids,
                label=support.label,
            )
            if support.label == VerificationLabel.SUPPORTED:
                accepted.append(claim)
        self.emit(
            run_id, "citation_validation_completed", "Claim citations validated",
            accepted=len(accepted), rejected=len(claims) - len(accepted),
        )
        return accepted

    @staticmethod
    def _citations(claims: list[Claim], evidence: list[RetrievedChunk]) -> list[Citation]:
        needed = {citation_id for claim in claims for citation_id in claim.citation_ids}
        return CragWorkflow._citations_for_ids(needed, evidence)

    @staticmethod
    def _citations_for_ids(needed: set[str], evidence: list[RetrievedChunk]) -> list[Citation]:
        return [
            Citation(
                id=item.citation_id, document_id=item.document_id, filename=item.filename,
                chunk_id=item.id, passage=item.text, anchor=item.anchor,
            )
            for item in evidence
            if item.citation_id in needed
        ]

    @staticmethod
    def _refusal(reason: str) -> AnswerResult:
        return AnswerResult(
            disposition="refused",
            summary="No reliable answer found.",
            refusal_reason=reason,
        )

    def _finish(self, run_id: str, result: AnswerResult, status: RunStatus) -> None:
        self.database.update_run(run_id, status=status, result_json=result.model_dump_json())
