from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.explainability.confidence import scores
from app.modules.explainability.enums import ExplainabilityRunStatus, ExplainabilityValidationStatus
from app.modules.explainability.exceptions import (
    ExplainabilityResolutionError,
    ExplainabilityVersionConflictError,
)
from app.modules.explainability.feature_importance import deterministic
from app.modules.explainability.lineage import build, fingerprint
from app.modules.explainability.models import (
    EvidenceReference,
    ExplainabilityRun,
    ExplainabilityValidationRecord,
    Explanation,
    FeatureContribution,
    ReasoningStep,
)
from app.modules.explainability.reasoning import chain
from app.modules.explainability.repositories import ExplainabilityRepository
from app.modules.explainability.schemas import ExplainabilityRunCreate
from app.modules.explainability.validation import validate


class ExplainabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ExplainabilityRepository(session)

    async def create_run(self, request: ExplainabilityRunCreate) -> ExplainabilityRun:
        probability = await self._repository.probability(request.probability_run_id)
        consensus = await self._repository.consensus(request.consensus_run_id)
        risk = await self._repository.risk(request.risk_run_id)
        if not probability or not consensus or not risk:
            raise ExplainabilityResolutionError(
                "Probability, Consensus, and Risk runs are required."
            )
        checksum = fingerprint(
            {
                "probability": probability.input_checksum,
                "consensus": consensus.input_checksum,
                "risk": risk.input_checksum,
                "parameters": request.parameters,
            }
        )
        key = fingerprint({"code": request.run_code, "input": checksum})
        if existing := await self._repository.existing(key):
            return existing
        if await self._repository.by_code(request.run_code):
            raise ExplainabilityVersionConflictError(
                "Explainability run code is immutable; use a new code for changed inputs."
            )
        findings = validate(probability, consensus, risk)
        valid = all(item.status is ExplainabilityValidationStatus.PASSED for item in findings)
        run = await self._repository.create(
            ExplainabilityRun(
                run_code=request.run_code,
                probability_run_id=probability.id,
                consensus_run_id=consensus.id,
                risk_run_id=risk.id,
                dataset_snapshot_id=probability.dataset_snapshot_id,
                feature_set_version_id=probability.feature_set_version_id,
                parameters=request.parameters,
                status=ExplainabilityRunStatus.COMPLETED
                if valid
                else ExplainabilityRunStatus.VALIDATION_FAILED,
                input_checksum=checksum,
                idempotency_key=key,
            )
        )
        self._session.add_all(
            [
                ExplainabilityValidationRecord(
                    explainability_run_id=run.id,
                    rule_name=item.rule_name,
                    status=item.status,
                    message=item.message,
                )
                for item in findings
            ]
        )
        self._session.add(build(run, probability))
        if not valid:
            return run
        probability_outputs = {
            (item.fixture_id, item.market_type, item.outcome): item
            for item in await self._repository.probability_outputs(probability.id)
        }
        consensus_outputs = {
            (item.fixture_id, item.market_type, item.outcome): item
            for item in await self._repository.consensus_outputs(consensus.id)
        }
        for risk_output in await self._repository.risk_outputs(risk.id):
            output_key = (risk_output.fixture_id, risk_output.market_type, risk_output.outcome)
            probability_output = probability_outputs.get(output_key)
            consensus_output = consensus_outputs.get(output_key)
            if not probability_output or not consensus_output:
                continue
            rows = await self._repository.feature_rows(
                run.dataset_snapshot_id, risk_output.fixture_id
            )
            contributions = deterministic(rows)
            confidence, evidence_score, traceability, coverage = scores(
                evidence_count=5 + len(rows), contribution_count=len(contributions)
            )
            summary = (
                f"Probability {probability_output.estimated_probability}, consensus "
                f"{consensus_output.consensus_probability}, and risk "
                f"{risk_output.overall_risk_score} are traced to immutable evidence."
            )
            explanation = Explanation(
                explainability_run_id=run.id,
                fixture_id=risk_output.fixture_id,
                market_type=risk_output.market_type,
                outcome=risk_output.outcome,
                explanation_summary=summary,
                confidence=_decimal(confidence),
                evidence_completeness=_decimal(evidence_score),
                traceability_score=_decimal(traceability),
                coverage_score=_decimal(coverage),
            )
            self._session.add(explanation)
            await self._session.flush()
            self._session.add_all(
                [
                    FeatureContribution(
                        explanation_id=explanation.id,
                        feature_id=item.feature_id,
                        feature_value=item.feature_value,
                        contribution=item.contribution,
                        direction=item.direction,
                        source_feature_value_id=item.source_feature_value_id,
                    )
                    for item in contributions
                ]
            )
            evidence = [
                ("dataset_snapshot", run.dataset_snapshot_id, "Frozen Research dataset."),
                ("probability_output", probability_output.id, "Probability estimate."),
                ("consensus_output", consensus_output.id, "Consensus evidence."),
                ("risk_output", risk_output.id, "Risk assessment."),
            ] + [
                ("feature_value", item.source_feature_value_id, "Feature contribution source.")
                for item in contributions
            ]
            self._session.add_all(
                [
                    EvidenceReference(
                        explanation_id=explanation.id,
                        sequence=index,
                        source_type=item[0],
                        source_id=str(item[1]),
                        description=item[2],
                    )
                    for index, item in enumerate(evidence, 1)
                ]
            )
            self._session.add_all(
                [
                    ReasoningStep(
                        explanation_id=explanation.id,
                        position=index,
                        stage=item[0],
                        description=item[1],
                        source_type=item[0],
                        source_id=item[2],
                    )
                    for index, item in enumerate(
                        chain(
                            dataset_id=run.dataset_snapshot_id,
                            probability_id=probability_output.id,
                            consensus_id=consensus_output.id,
                            risk_id=risk_output.id,
                        ),
                        1,
                    )
                ]
            )
        return run


def _decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.00000001"))
