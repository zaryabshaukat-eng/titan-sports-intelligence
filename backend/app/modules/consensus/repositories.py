"""Async persistence boundary for Consensus artifacts and immutable Probability evidence."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.models import (
    ConsensusLineage,
    ConsensusOutput,
    ConsensusRun,
    ConsensusValidationRecord,
)
from app.modules.consensus.schemas import PaginationParams
from app.modules.probability.models import ProbabilityEvaluation, ProbabilityOutput, ProbabilityRun


class ConsensusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def probability_runs(self, identifiers: Sequence[UUID]) -> list[ProbabilityRun]:
        return (
            list(
                (
                    await self._session.scalars(
                        select(ProbabilityRun).where(ProbabilityRun.id.in_(identifiers))
                    )
                ).all()
            )
            if identifiers
            else []
        )

    async def probability_outputs(self, identifiers: Sequence[UUID]) -> list[ProbabilityOutput]:
        return (
            list(
                (
                    await self._session.scalars(
                        select(ProbabilityOutput).where(
                            ProbabilityOutput.probability_run_id.in_(identifiers)
                        )
                    )
                ).all()
            )
            if identifiers
            else []
        )

    async def latest_evaluations(self, identifiers: Sequence[UUID]) -> list[ProbabilityEvaluation]:
        return (
            list(
                (
                    await self._session.scalars(
                        select(ProbabilityEvaluation)
                        .where(ProbabilityEvaluation.probability_run_id.in_(identifiers))
                        .order_by(ProbabilityEvaluation.created_at.desc())
                    )
                ).all()
            )
            if identifiers
            else []
        )

    async def existing_run(self, key: str) -> ConsensusRun | None:
        return await self._session.scalar(
            select(ConsensusRun).where(ConsensusRun.idempotency_key == key)
        )

    async def run_by_code(self, code: str) -> ConsensusRun | None:
        return await self._session.scalar(select(ConsensusRun).where(ConsensusRun.run_code == code))

    async def create_run(self, run: ConsensusRun) -> ConsensusRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def list_runs(self, pagination: PaginationParams) -> tuple[list[ConsensusRun], int]:
        return await self._page(
            select(ConsensusRun).order_by(ConsensusRun.created_at.desc()), pagination
        )

    async def outputs(self, run_id: UUID) -> list[ConsensusOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ConsensusOutput)
                    .where(ConsensusOutput.consensus_run_id == run_id)
                    .order_by(ConsensusOutput.fixture_id, ConsensusOutput.market_type)
                )
            ).all()
        )

    async def lineage(self, run_id: UUID) -> ConsensusLineage | None:
        return await self._session.scalar(
            select(ConsensusLineage).where(ConsensusLineage.consensus_run_id == run_id)
        )

    async def validation(self, run_id: UUID) -> list[ConsensusValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(ConsensusValidationRecord)
                    .where(ConsensusValidationRecord.consensus_run_id == run_id)
                    .order_by(ConsensusValidationRecord.rule_name)
                )
            ).all()
        )

    async def _page[EntityT](
        self, statement: Select[tuple[EntityT]], pagination: PaginationParams
    ) -> tuple[list[EntityT], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        rows = list(
            (
                await self._session.scalars(
                    statement.offset(pagination.offset).limit(pagination.limit)
                )
            ).all()
        )
        return rows, total or 0
