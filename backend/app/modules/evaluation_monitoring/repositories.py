from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.models import BacktestMetric, BacktestRun
from app.modules.evaluation_monitoring.models import (
    EvaluationConfiguration,
    EvaluationRun,
    ModelHealth,
    RunArtifact,
)
from app.modules.probability.models import ProbabilityRun


class MonitoringRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def backtest(self, id: UUID) -> BacktestRun | None:
        return await self.s.get(BacktestRun, id)

    async def probability(self, id: UUID) -> ProbabilityRun | None:
        return await self.s.get(ProbabilityRun, id)

    async def metric(self, id: UUID) -> BacktestMetric | None:
        return await self.s.scalar(
            select(BacktestMetric).where(BacktestMetric.backtest_run_id == id)
        )

    async def existing(self, key: str) -> EvaluationRun | None:
        return await self.s.scalar(
            select(EvaluationRun).where(EvaluationRun.idempotency_key == key)
        )

    async def by_code(self, code: str) -> EvaluationRun | None:
        return await self.s.scalar(select(EvaluationRun).where(EvaluationRun.run_code == code))

    async def configuration(self, code: str, version: str) -> EvaluationConfiguration | None:
        return await self.s.scalar(
            select(EvaluationConfiguration).where(
                EvaluationConfiguration.configuration_code == code,
                EvaluationConfiguration.version == version,
            )
        )

    async def run(self, id: UUID) -> EvaluationRun | None:
        return await self.s.get(EvaluationRun, id)

    async def runs(self) -> list[EvaluationRun]:
        return list(
            (
                await self.s.scalars(
                    select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
                )
            ).all()
        )

    async def latest(self, exclude: UUID) -> EvaluationRun | None:
        return await self.s.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.id != exclude, EvaluationRun.status == "completed")
            .order_by(EvaluationRun.created_at.desc())
        )

    async def model_health(self, run_id: UUID) -> ModelHealth | None:
        return await self.s.scalar(
            select(ModelHealth).where(ModelHealth.evaluation_run_id == run_id)
        )

    async def add(self, value: object) -> None:
        self.s.add(value)

    async def flush(self) -> None:
        await self.s.flush()

    async def list_for(self, model: type[RunArtifact], run_id: UUID) -> list[RunArtifact]:
        return list(
            (await self.s.scalars(select(model).where(model.evaluation_run_id == run_id))).all()
        )
