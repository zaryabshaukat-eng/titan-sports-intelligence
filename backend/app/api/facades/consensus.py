"""Thin API facade preserving Consensus Engine dependency boundaries."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.engines import StrategyMetadata
from app.modules.consensus.models import (
    ConsensusLineage,
    ConsensusOutput,
    ConsensusRun,
    ConsensusValidationRecord,
)
from app.modules.consensus.registry import ConsensusStrategyRegistry
from app.modules.consensus.repositories import ConsensusRepository
from app.modules.consensus.schemas import ConsensusRunCreate, PaginationParams
from app.modules.consensus.service import ConsensusService


class ConsensusApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = ConsensusRepository(session), ConsensusService(session)

    @staticmethod
    def strategies() -> list[StrategyMetadata]:
        return ConsensusStrategyRegistry().metadata()

    async def create_run(self, body: ConsensusRunCreate) -> ConsensusRun:
        return await self._service.create_run(body)

    async def runs(self, page: PaginationParams) -> tuple[list[ConsensusRun], int]:
        return await self._reads.list_runs(page)

    async def outputs(self, id: UUID) -> list[ConsensusOutput]:
        return await self._reads.outputs(id)

    async def lineage(self, id: UUID) -> ConsensusLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[ConsensusValidationRecord]:
        return await self._reads.validation(id)
