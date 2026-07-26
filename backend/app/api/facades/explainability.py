"""Thin API facade preserving Explainability Engine dependencies."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.explainability.engines import DeterministicFeatureExplainer
from app.modules.explainability.models import (
    EvidenceReference,
    ExplainabilityLineage,
    ExplainabilityRun,
    ExplainabilityValidationRecord,
    Explanation,
    FeatureContribution,
    ReasoningStep,
)
from app.modules.explainability.registry import ExplainabilityRegistry
from app.modules.explainability.repositories import ExplainabilityRepository
from app.modules.explainability.schemas import ExplainabilityRunCreate
from app.modules.explainability.service import ExplainabilityService


class ExplainabilityApiFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._reads, self._service = (
            ExplainabilityRepository(session),
            ExplainabilityService(session),
        )

    @staticmethod
    def engines() -> tuple[DeterministicFeatureExplainer, ...]:
        return ExplainabilityRegistry().engines()

    async def create_run(self, body: ExplainabilityRunCreate) -> ExplainabilityRun:
        return await self._service.create_run(body)

    async def explanations(self, id: UUID) -> list[Explanation]:
        return await self._reads.explanations(id)

    async def contributions(self, id: UUID) -> list[FeatureContribution]:
        return await self._reads.contributions(id)

    async def evidence(self, id: UUID) -> list[EvidenceReference]:
        return await self._reads.evidence(id)

    async def reasoning(self, id: UUID) -> list[ReasoningStep]:
        return await self._reads.reasoning(id)

    async def lineage(self, id: UUID) -> ExplainabilityLineage | None:
        return await self._reads.lineage(id)

    async def validation(self, id: UUID) -> list[ExplainabilityValidationRecord]:
        return await self._reads.validation(id)
