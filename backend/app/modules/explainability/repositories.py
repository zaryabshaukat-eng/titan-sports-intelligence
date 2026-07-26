from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.models import ConsensusOutput, ConsensusRun
from app.modules.explainability.models import (
    EvidenceReference,
    ExplainabilityLineage,
    ExplainabilityRun,
    ExplainabilityValidationRecord,
    Explanation,
    FeatureContribution,
    ReasoningStep,
)
from app.modules.probability.models import ProbabilityOutput, ProbabilityRun
from app.modules.research.models import DatasetSnapshotRow
from app.modules.risk.models import RiskOutput, RiskRun


class ExplainabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def probability(self, id: UUID) -> ProbabilityRun | None:
        return await self._session.get(ProbabilityRun, id)

    async def consensus(self, id: UUID) -> ConsensusRun | None:
        return await self._session.get(ConsensusRun, id)

    async def risk(self, id: UUID) -> RiskRun | None:
        return await self._session.get(RiskRun, id)

    async def probability_outputs(self, id: UUID) -> list[ProbabilityOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ProbabilityOutput).where(ProbabilityOutput.probability_run_id == id)
                )
            ).all()
        )

    async def consensus_outputs(self, id: UUID) -> list[ConsensusOutput]:
        return list(
            (
                await self._session.scalars(
                    select(ConsensusOutput).where(ConsensusOutput.consensus_run_id == id)
                )
            ).all()
        )

    async def risk_outputs(self, id: UUID) -> list[RiskOutput]:
        return list(
            (
                await self._session.scalars(select(RiskOutput).where(RiskOutput.risk_run_id == id))
            ).all()
        )

    async def feature_rows(self, dataset: UUID, fixture: UUID) -> list[DatasetSnapshotRow]:
        return list(
            (
                await self._session.scalars(
                    select(DatasetSnapshotRow).where(
                        DatasetSnapshotRow.dataset_snapshot_id == dataset,
                        DatasetSnapshotRow.fixture_id == fixture,
                    )
                )
            ).all()
        )

    async def existing(self, key: str) -> ExplainabilityRun | None:
        return await self._session.scalar(
            select(ExplainabilityRun).where(ExplainabilityRun.idempotency_key == key)
        )

    async def by_code(self, code: str) -> ExplainabilityRun | None:
        return await self._session.scalar(
            select(ExplainabilityRun).where(ExplainabilityRun.run_code == code)
        )

    async def create(self, run: ExplainabilityRun) -> ExplainabilityRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def explanations(self, run: UUID) -> list[Explanation]:
        return list(
            (
                await self._session.scalars(
                    select(Explanation).where(Explanation.explainability_run_id == run)
                )
            ).all()
        )

    async def contributions(self, id: UUID) -> list[FeatureContribution]:
        return list(
            (
                await self._session.scalars(
                    select(FeatureContribution).where(FeatureContribution.explanation_id == id)
                )
            ).all()
        )

    async def evidence(self, id: UUID) -> list[EvidenceReference]:
        return list(
            (
                await self._session.scalars(
                    select(EvidenceReference).where(EvidenceReference.explanation_id == id)
                )
            ).all()
        )

    async def reasoning(self, id: UUID) -> list[ReasoningStep]:
        return list(
            (
                await self._session.scalars(
                    select(ReasoningStep).where(ReasoningStep.explanation_id == id)
                )
            ).all()
        )

    async def lineage(self, id: UUID) -> ExplainabilityLineage | None:
        return await self._session.scalar(
            select(ExplainabilityLineage).where(ExplainabilityLineage.explainability_run_id == id)
        )

    async def validation(self, id: UUID) -> list[ExplainabilityValidationRecord]:
        return list(
            (
                await self._session.scalars(
                    select(ExplainabilityValidationRecord).where(
                        ExplainabilityValidationRecord.explainability_run_id == id
                    )
                )
            ).all()
        )
