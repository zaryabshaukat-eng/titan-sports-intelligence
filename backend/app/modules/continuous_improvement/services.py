from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.continuous_improvement.enums import ImprovementStatus, RecommendationType
from app.modules.continuous_improvement.models import (
    ImprovementConfiguration,
    ImprovementRun,
    LineageRecord,
    Recommendation,
    RecommendationEvidence,
    ValidationRecord,
)
from app.modules.continuous_improvement.registry import ImprovementAnalyzerRegistry
from app.modules.continuous_improvement.repositories import ImprovementRepository
from app.modules.continuous_improvement.schemas import RunCreate
from app.modules.evaluation.lineage import fingerprint


class ImprovementService:
    def __init__(self, s: AsyncSession):
        self.s = s
        self.r = ImprovementRepository(s)
        self.registry = ImprovementAnalyzerRegistry()

    async def run(self, x: RunCreate):
        bt = await self.r.backtest(x.backtest_run_id)
        ev = await self.r.evaluation(x.evaluation_run_id)
        if not bt or not ev or ev.backtest_run_id != bt.id:
            raise ValueError("immutable evaluation and backtest lineage must match")
        key = fingerprint(
            {
                "backtest": bt.input_checksum,
                "evaluation": ev.input_checksum,
                "thresholds": x.thresholds,
            }
        )
        if old := await self.r.existing(key):
            return old
        config = ImprovementConfiguration(
            code=x.configuration_code,
            version=x.configuration_version,
            analyzer_versions={a.identifier: "1" for a in self.registry.analyzers()},
            thresholds=x.thresholds,
            checksum=fingerprint(
                {
                    "code": x.configuration_code,
                    "version": x.configuration_version,
                    "thresholds": x.thresholds,
                }
            ),
        )
        self.s.add(config)
        await self.s.flush()
        run = ImprovementRun(
            run_code=x.run_code,
            configuration_id=config.id,
            evaluation_run_id=ev.id,
            backtest_run_id=bt.id,
            status=ImprovementStatus.COMPLETED,
            input_checksum=key,
            idempotency_key=key,
        )
        self.s.add(run)
        await self.s.flush()
        recs = []
        for a in self.registry.analyzers():
            r = Recommendation(
                improvement_run_id=run.id,
                recommendation_type=RecommendationType(a.recommendation_type),
                title=a.identifier.replace("_", " ").title(),
                rationale=a.description,
                confidence=0.5,
                analyzer_id=a.identifier,
                payload={"advisory_only": True, "input_checksum": key},
            )
            self.s.add(r)
            await self.s.flush()
            recs.append(
                RecommendationEvidence(
                    improvement_run_id=run.id,
                    recommendation_id=r.id,
                    evidence={"evaluation_run_id": str(ev.id), "backtest_run_id": str(bt.id)},
                )
            )
        recs.extend(
            (
                ValidationRecord(
                    improvement_run_id=run.id,
                    rule_name="advisory_only",
                    status="passed",
                    message="No deployment, retraining, or source mutation is possible.",
                ),
                LineageRecord(
                    improvement_run_id=run.id,
                    artifact_ids={
                        "evaluation_run_id": str(ev.id),
                        "backtest_run_id": str(bt.id),
                        "feature_set_version_id": str(bt.feature_set_version_id),
                        "dataset_snapshot_id": str(bt.dataset_snapshot_id),
                        "probability_run_id": str(bt.probability_run_id),
                        "consensus_run_id": str(bt.consensus_run_id),
                        "risk_run_id": str(bt.risk_run_id),
                        "explainability_run_id": str(bt.explainability_run_id),
                    },
                    checksum=key,
                ),
            )
        )
        self.s.add_all(recs)
        return run
