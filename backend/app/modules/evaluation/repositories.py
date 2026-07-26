from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.models import ConsensusRun
from app.modules.evaluation.models import (
    BacktestLineage,
    BacktestMetric,
    BacktestResult,
    BacktestRun,
    BacktestValidationRecord,
)
from app.modules.evaluation.schemas import PaginationParams
from app.modules.explainability.models import ExplainabilityRun
from app.modules.probability.models import ProbabilityOutput, ProbabilityRun
from app.modules.risk.models import RiskRun
from app.modules.sports.models import Fixture


class EvaluationRepository:
    def __init__(self, s: AsyncSession) -> None:
        self._session = s

    async def probability(self, id: UUID) -> ProbabilityRun | None:
        return await self._session.get(ProbabilityRun, id)

    async def consensus(self, id: UUID) -> ConsensusRun | None:
        return await self._session.get(ConsensusRun, id)

    async def risk(self, id: UUID) -> RiskRun | None:
        return await self._session.get(RiskRun, id)

    async def explainability(self, id: UUID) -> ExplainabilityRun | None:
        return await self._session.get(ExplainabilityRun, id)

    async def outputs(self, ids: list[UUID]) -> list[ProbabilityOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityOutput).where(ProbabilityOutput.id.in_(ids))
                )
            ).all()
        )

    async def fixtures(self, ids: list[UUID]) -> dict[UUID, Fixture]:
        """Resolve fixtures in one query so large replays do not incur N+1 lookups."""
        values = list(
            (await self._session.scalars(select(Fixture).where(Fixture.id.in_(ids)))).all()
        )
        return {item.id: item for item in values}

    async def existing(self, key: str) -> BacktestRun | None:
        return await self._session.scalar(
            select(BacktestRun).where(BacktestRun.idempotency_key == key)
        )

    async def by_code(self, code: str) -> BacktestRun | None:
        return await self._session.scalar(select(BacktestRun).where(BacktestRun.run_code == code))

    async def run(self, id: UUID) -> BacktestRun | None:
        return await self._session.get(BacktestRun, id)

    async def list_runs(self, pagination: PaginationParams) -> tuple[list[BacktestRun], int]:
        statement = (
            select(BacktestRun)
            .order_by(BacktestRun.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self._session.scalars(statement)).all())
        total = await self._session.scalar(select(func.count()).select_from(BacktestRun))
        return items, int(total or 0)

    async def create(self, run: BacktestRun) -> BacktestRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def results(self, id: UUID) -> list[BacktestResult]:
        return list(
            (
                await self._session.scalars(
                    select(BacktestResult)
                    .where(BacktestResult.backtest_run_id == id)
                    .order_by(BacktestResult.fixture_start_at, BacktestResult.created_at)
                )
            ).all()
        )

    async def metric(self, id: UUID) -> BacktestMetric | None:
        return await self._session.scalar(
            select(BacktestMetric).where(BacktestMetric.backtest_run_id == id)
        )

    async def comparison_metrics(self, ids: list[UUID]) -> dict[UUID, BacktestMetric]:
        items = list(
            (
                await self._session.scalars(
                    select(BacktestMetric).where(BacktestMetric.backtest_run_id.in_(ids))
                )
            ).all()
        )
        return {item.backtest_run_id: item for item in items}

    async def lineage(self, id: UUID) -> BacktestLineage | None:
        return await self._session.scalar(
            select(BacktestLineage).where(BacktestLineage.backtest_run_id == id)
        )

    async def validation(self, id: UUID) -> list[BacktestValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(BacktestValidationRecord).where(
                        BacktestValidationRecord.backtest_run_id == id
                    )
                )
            ).all()
        )
