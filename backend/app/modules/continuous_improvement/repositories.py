from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.continuous_improvement.models import (
    ImprovementRun,
)
from app.modules.evaluation.models import BacktestRun
from app.modules.evaluation_monitoring.models import EvaluationRun


class ImprovementRepository:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def backtest(self, id: UUID):
        return await self.s.get(BacktestRun, id)

    async def evaluation(self, id: UUID):
        return await self.s.get(EvaluationRun, id)

    async def existing(self, key: str):
        return await self.s.scalar(
            select(ImprovementRun).where(ImprovementRun.idempotency_key == key)
        )

    async def run(self, id: UUID):
        return await self.s.get(ImprovementRun, id)

    async def runs(self):
        return list(
            (
                await self.s.scalars(
                    select(ImprovementRun).order_by(ImprovementRun.created_at.desc())
                )
            ).all()
        )

    async def for_run(self, model, id: UUID):
        return list(
            (await self.s.scalars(select(model).where(model.improvement_run_id == id))).all()
        )
