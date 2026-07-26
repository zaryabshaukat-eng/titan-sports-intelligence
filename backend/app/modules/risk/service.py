from decimal import Decimal
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.risk.engines import RiskContext
from app.modules.risk.enums import RiskRunStatus, RiskValidationStatus
from app.modules.risk.exceptions import RiskResolutionError, RiskVersionConflictError
from app.modules.risk.lineage import build, fingerprint
from app.modules.risk.models import RiskOutput, RiskRun, RiskValidationRecord
from app.modules.risk.registry import RiskAnalyzerRegistry
from app.modules.risk.repositories import RiskRepository
from app.modules.risk.schemas import RiskRunCreate
from app.modules.risk.validation import validate


class RiskService:
    def __init__(self, session: AsyncSession, registry: RiskAnalyzerRegistry | None = None) -> None:
        self._session = session
        self._repository = RiskRepository(session)
        self._registry = registry or RiskAnalyzerRegistry()

    async def create_run(self, request: RiskRunCreate) -> RiskRun:
        consensus = await self._repository.consensus(request.consensus_run_id)
        if consensus is None:
            raise RiskResolutionError("Consensus run was not found.")
        outputs = await self._repository.consensus_outputs(consensus.id)
        lineage = await self._repository.consensus_lineage(consensus.id)
        checksum = fingerprint(
            {
                "consensus": consensus.input_checksum,
                "parameters": request.parameters,
                "seed": request.random_seed,
            }
        )
        key = fingerprint({"code": request.run_code, "input": checksum})
        if existing := await self._repository.existing(key):
            return existing
        if await self._repository.by_code(request.run_code):
            raise RiskVersionConflictError(
                "Risk run code is immutable; use a new code for changed inputs."
            )
        findings = validate(consensus, outputs, lineage)
        valid = all(item.status is RiskValidationStatus.PASSED for item in findings)
        run = await self._repository.create(
            RiskRun(
                run_code=request.run_code,
                consensus_run_id=consensus.id,
                dataset_snapshot_id=consensus.dataset_snapshot_id,
                feature_set_version_id=consensus.feature_set_version_id,
                parameters=request.parameters,
                random_seed=request.random_seed,
                status=RiskRunStatus.COMPLETED if valid else RiskRunStatus.VALIDATION_FAILED,
                input_checksum=checksum,
                idempotency_key=key,
            )
        )
        self._session.add_all(
            [
                RiskValidationRecord(
                    risk_run_id=run.id,
                    rule_name=item.rule_name,
                    status=item.status,
                    message=item.message,
                )
                for item in findings
            ]
        )
        if lineage:
            self._session.add(
                build(
                    risk_run_id=run.id,
                    consensus=consensus,
                    probability_run_ids=lineage.probability_run_ids,
                    parameters=request.parameters,
                    seed=request.random_seed,
                )
            )
        if not valid:
            return run
        analyzers = {item.metadata.identifier: item for item in self._registry.analyzers()}
        results: list[RiskOutput] = []
        for output in outputs:
            context = RiskContext(
                float(output.consensus_probability),
                output.confidence_metrics,
                output.disagreement_metrics,
                output.contributor_count,
                output.expected_count,
                float(cast(str | float, output.confidence_metrics.get("calibration_quality", 0.5))),
            )
            values = {
                name: analyzer.assess(context, request.parameters)
                for name, analyzer in analyzers.items()
            }
            overall = sum(values.values()) / len(values)
            completeness = 1 - values["data_quality_risk"]
            results.append(
                RiskOutput(
                    risk_run_id=run.id,
                    fixture_id=output.fixture_id,
                    market_type=output.market_type,
                    outcome=output.outcome,
                    overall_risk_score=_decimal(overall),
                    uncertainty_score=_decimal(values["uncertainty"]),
                    stability_score=_decimal(values["stability"]),
                    calibration_risk=_decimal(values["calibration_risk"]),
                    agreement_risk=_decimal(values["agreement_risk"]),
                    data_quality_risk=_decimal(values["data_quality_risk"]),
                    completeness_score=_decimal(completeness),
                    components=values,
                )
            )
        self._session.add_all(results)
        return run


def _decimal(value: float) -> Decimal:
    return Decimal(str(min(1.0, max(0.0, value)))).quantize(Decimal("0.00000001"))
