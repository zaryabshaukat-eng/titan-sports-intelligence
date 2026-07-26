"""Thin API facade preserving Risk Engine dependencies."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.risk.engines import RiskAnalyzer
from app.modules.risk.models import RiskLineage, RiskOutput, RiskRun, RiskValidationRecord
from app.modules.risk.registry import RiskAnalyzerRegistry
from app.modules.risk.repositories import RiskRepository
from app.modules.risk.schemas import RiskRunCreate
from app.modules.risk.service import RiskService


class RiskApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = RiskRepository(session), RiskService(session)

    @staticmethod
    def analyzers() -> list[RiskAnalyzer]:
        return RiskAnalyzerRegistry().analyzers()

    async def create_run(self, body: RiskRunCreate) -> RiskRun:
        return await self._service.create_run(body)

    async def outputs(self, id: UUID) -> list[RiskOutput]:
        return await self._reads.outputs(id)

    async def lineage(self, id: UUID) -> RiskLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[RiskValidationRecord]:
        return await self._reads.validation(id)
