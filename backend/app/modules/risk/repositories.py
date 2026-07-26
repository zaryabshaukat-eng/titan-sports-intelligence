from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.models import ConsensusLineage, ConsensusOutput, ConsensusRun
from app.modules.risk.models import RiskLineage, RiskOutput, RiskRun, RiskValidationRecord


class RiskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def consensus(self, identifier: UUID) -> ConsensusRun | None:
        return await self._session.get(ConsensusRun, identifier)

    async def consensus_outputs(self, identifier: UUID) -> list[ConsensusOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ConsensusOutput).where(ConsensusOutput.consensus_run_id == identifier)
                )
            ).all()
        )

    async def consensus_lineage(self, identifier: UUID) -> ConsensusLineage | None:
        return await self._session.scalar(
            select(ConsensusLineage).where(ConsensusLineage.consensus_run_id == identifier)
        )

    async def existing(self, key: str) -> RiskRun | None:
        return await self._session.scalar(select(RiskRun).where(RiskRun.idempotency_key == key))

    async def by_code(self, code: str) -> RiskRun | None:
        return await self._session.scalar(select(RiskRun).where(RiskRun.run_code == code))

    async def create(self, run: RiskRun) -> RiskRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def outputs(self, identifier: UUID) -> list[RiskOutput]:
        return list(
            (
                await self._session.scalars(
                    select(RiskOutput).where(RiskOutput.risk_run_id == identifier)
                )
            ).all()
        )

    async def lineage(self, identifier: UUID) -> RiskLineage | None:
        return await self._session.scalar(
            select(RiskLineage).where(RiskLineage.risk_run_id == identifier)
        )

    async def validation(self, identifier: UUID) -> list[RiskValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(RiskValidationRecord).where(
                        RiskValidationRecord.risk_run_id == identifier
                    )
                )
            ).all()
        )
