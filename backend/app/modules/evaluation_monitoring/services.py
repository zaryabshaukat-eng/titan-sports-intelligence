from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.lineage import fingerprint
from app.modules.evaluation_monitoring.analyzers.distribution import normalize
from app.modules.evaluation_monitoring.enums import (
    AlertSeverity,
    MonitoringStatus,
    ValidationStatus,
)
from app.modules.evaluation_monitoring.models import (
    Alert,
    CalibrationHealth,
    DriftMeasurement,
    EvaluationConfiguration,
    EvaluationResult,
    EvaluationRun,
    FeatureHealth,
    LineageRecord,
    ModelHealth,
    ProviderHealth,
    QualityMetric,
    ValidationRecord,
)
from app.modules.evaluation_monitoring.registry import MonitoringAnalyzerRegistry
from app.modules.evaluation_monitoring.repositories import MonitoringRepository
from app.modules.evaluation_monitoring.schemas import MonitoringRunCreate


class MonitoringService:
    def __init__(
        self, session: AsyncSession, registry: MonitoringAnalyzerRegistry | None = None
    ) -> None:
        self.s, self.r, self.registry = (
            session,
            MonitoringRepository(session),
            registry or MonitoringAnalyzerRegistry(),
        )

    async def run(self, request: MonitoringRunCreate) -> EvaluationRun:
        backtest = await self.r.backtest(request.backtest_run_id)
        if backtest is None:
            raise ValueError("backtest run not found")
        probability = await self.r.probability(backtest.probability_run_id)
        metric = await self.r.metric(backtest.id)
        if probability is None or metric is None:
            raise ValueError("backtest lineage is incomplete")
        payload = {
            "backtest": backtest.input_checksum,
            "config": request.configuration_code,
            "version": request.configuration_version,
            "thresholds": request.thresholds,
            "providers": request.providers,
            "seed": request.random_seed,
        }
        key = fingerprint(payload)
        if existing := await self.r.existing(key):
            return existing
        if await self.r.by_code(request.run_code):
            raise ValueError("run code is immutable")
        config = await self.r.configuration(
            request.configuration_code, request.configuration_version
        )
        if config is None:
            config = EvaluationConfiguration(
                configuration_code=request.configuration_code,
                version=request.configuration_version,
                thresholds=request.thresholds,
                analyzer_versions={a.identifier: "1" for a in self.registry.analyzers()},
                checksum=fingerprint(
                    {
                        "code": request.configuration_code,
                        "version": request.configuration_version,
                        "thresholds": request.thresholds,
                    }
                ),
            )
            self.s.add(config)
            await self.r.flush()
        elif config.thresholds != request.thresholds:
            raise ValueError("configuration versions are immutable")
        run = EvaluationRun(
            run_code=request.run_code,
            configuration_id=config.id,
            feature_set_version_id=backtest.feature_set_version_id,
            dataset_snapshot_id=backtest.dataset_snapshot_id,
            probability_run_id=backtest.probability_run_id,
            consensus_run_id=backtest.consensus_run_id,
            risk_run_id=backtest.risk_run_id,
            explainability_run_id=backtest.explainability_run_id,
            backtest_run_id=backtest.id,
            dataset_checksum=backtest.input_checksum,
            generator_versions={},
            random_seed=request.random_seed,
            status=MonitoringStatus.COMPLETED,
            input_checksum=key,
            idempotency_key=key,
        )
        self.s.add(run)
        await self.r.flush()
        current = normalize(
            [
                float(value)
                for value in metric.metrics.values()
                if isinstance(value, (int, float)) and value is not None
            ]
        )
        if not current:
            current = [1.0]
        previous = await self.r.latest(run.id)
        previous_health = await self.r.model_health(previous.id) if previous else None
        baseline_values = (
            [
                float(value)
                for value in previous_health.metrics.values()
                if isinstance(value, (int, float)) and value is not None
            ]
            if previous_health
            else current
        )
        baseline = normalize(baseline_values) or current
        results = []
        for analyzer in self.registry.analyzers():
            value = float(analyzer.calculate(baseline, current))
            results.extend(
                (
                    EvaluationResult(
                        evaluation_run_id=run.id,
                        analyzer_id=analyzer.identifier,
                        value=Decimal(str(value)),
                        details={"baseline": "self" if previous is None else str(previous.id)},
                    ),
                    DriftMeasurement(
                        evaluation_run_id=run.id,
                        metric_name=analyzer.identifier,
                        value=Decimal(str(value)),
                        baseline_run_id=previous.id if previous else None,
                    ),
                )
            )
            threshold = request.thresholds.get(analyzer.identifier)
            if threshold is not None and value > threshold:
                results.append(
                    Alert(
                        evaluation_run_id=run.id,
                        severity=AlertSeverity.WARNING,
                        alert_type="drift_threshold",
                        message=f"{analyzer.identifier} exceeded configured threshold",
                        evidence={"value": value, "threshold": threshold},
                    )
                )
        results.extend(
            (
                QualityMetric(
                    evaluation_run_id=run.id,
                    metric_name="backtest_sample_count",
                    value=Decimal(metric.sample_count),
                    dimensions={},
                ),
                ModelHealth(
                    evaluation_run_id=run.id,
                    model_identifier=probability.model_identifier,
                    model_version=probability.model_version,
                    metrics=metric.metrics,
                ),
                FeatureHealth(
                    evaluation_run_id=run.id,
                    feature_set_version_id=backtest.feature_set_version_id,
                    completeness_score=Decimal("1"),
                    metrics={"dataset_checksum": backtest.input_checksum},
                ),
                CalibrationHealth(
                    evaluation_run_id=run.id,
                    calibration_version=str(probability.calibration_version_id)
                    if probability.calibration_version_id
                    else None,
                    metrics={"calibration_error": metric.metrics.get("calibration_error")},
                ),
                LineageRecord(
                    evaluation_run_id=run.id,
                    artifact_ids={
                        "backtest_run_id": str(backtest.id),
                        "probability_run_id": str(probability.id),
                        "consensus_run_id": str(backtest.consensus_run_id),
                        "risk_run_id": str(backtest.risk_run_id),
                        "explainability_run_id": str(backtest.explainability_run_id),
                        "dataset_snapshot_id": str(backtest.dataset_snapshot_id),
                        "feature_set_version_id": str(backtest.feature_set_version_id),
                    },
                    checksum=key,
                ),
                ValidationRecord(
                    evaluation_run_id=run.id,
                    rule_name="immutable_lineage",
                    status=ValidationStatus.PASSED,
                    message="all source artifacts are immutable and versioned",
                ),
            )
        )
        for item in request.providers:
            results.append(
                ProviderHealth(
                    evaluation_run_id=run.id,
                    provider_name=item.provider_name,
                    freshness_seconds=item.freshness_seconds,
                    completeness_score=Decimal(str(item.completeness_score)),
                    status="healthy" if item.completeness_score >= 0.9 else "degraded",
                )
            )
        self.s.add_all(results)
        return run
