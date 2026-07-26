from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.continuous_improvement.models import Artifact, ImprovementRun
from app.modules.continuous_improvement.repositories import ImprovementRepository
from app.modules.continuous_improvement.schemas import RunCreate
from app.modules.continuous_improvement.services import ImprovementService


class ImprovementApiFacade:
    def __init__(self, s: AsyncSession) -> None:
        self._reads, self._service = ImprovementRepository(s), ImprovementService(s)

    async def run(self, b: RunCreate) -> ImprovementRun:
        return await self._service.run(b)

    async def runs(self) -> list[ImprovementRun]:
        return await self._reads.runs()

    async def get(self, id: UUID) -> ImprovementRun | None:
        return await self._reads.run(id)

    async def items(self, m: type[Artifact], id: UUID) -> list[Artifact]:
        return await self._reads.for_run(m, id)
