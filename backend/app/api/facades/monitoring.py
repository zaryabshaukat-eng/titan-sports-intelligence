from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation_monitoring.models import EvaluationRun, RunArtifact
from app.modules.evaluation_monitoring.repositories import MonitoringRepository
from app.modules.evaluation_monitoring.schemas import MonitoringRunCreate
from app.modules.evaluation_monitoring.services import MonitoringService


class MonitoringApiFacade:
    def __init__(self, s: AsyncSession) -> None:
        self._reads, self._service = MonitoringRepository(s), MonitoringService(s)

    async def run(self, b: MonitoringRunCreate) -> EvaluationRun:
        return await self._service.run(b)

    async def runs(self) -> list[EvaluationRun]:
        return await self._reads.runs()

    async def get(self, id: UUID) -> EvaluationRun | None:
        return await self._reads.run(id)

    async def items(self, m: type[RunArtifact], id: UUID) -> list[RunArtifact]:
        return await self._reads.list_for(m, id)
