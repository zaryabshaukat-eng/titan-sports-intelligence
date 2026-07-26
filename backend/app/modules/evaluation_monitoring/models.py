from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.evaluation_monitoring.enums import AlertSeverity, MonitoringStatus, ValidationStatus
from app.shared.persistence.base import Base


class IdCreated:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvaluationConfiguration(IdCreated, Base):
    __tablename__ = "monitoring_evaluation_configurations"
    __table_args__ = (UniqueConstraint("configuration_code", "version", name="uq_monitoring_configuration_version"),)
    configuration_code: Mapped[str] = mapped_column(String(96), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    thresholds: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    analyzer_versions: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class EvaluationRun(IdCreated, Base):
    __tablename__ = "monitoring_evaluation_runs"
    __table_args__ = (UniqueConstraint("run_code", name="uq_monitoring_run_code"), UniqueConstraint("idempotency_key", name="uq_monitoring_run_key"), Index("ix_monitoring_runs_backtest_created", "backtest_run_id", "created_at"))
    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    configuration_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("monitoring_evaluation_configurations.id", ondelete="RESTRICT"), nullable=False, index=True)
    feature_set_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"), nullable=False, index=True)
    dataset_snapshot_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True)
    probability_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("probability_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    consensus_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("consensus_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    risk_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("risk_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    explainability_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("explainability_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    backtest_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="RESTRICT"), nullable=False, index=True)
    dataset_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_versions: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[MonitoringStatus] = mapped_column(SqlEnum(MonitoringStatus, name="monitoring_status"), nullable=False)
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class RunArtifact(IdCreated, Base):
    __abstract__ = True
    evaluation_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"), nullable=False, index=True)


class EvaluationResult(RunArtifact):
    __tablename__ = "monitoring_evaluation_results"
    analyzer_id: Mapped[str] = mapped_column(String(96), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class DriftMeasurement(RunArtifact):
    __tablename__ = "monitoring_drift_measurements"
    metric_name: Mapped[str] = mapped_column(String(96), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    baseline_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"))


class QualityMetric(RunArtifact):
    __tablename__ = "monitoring_quality_metrics"
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    dimensions: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class ProviderHealth(RunArtifact):
    __tablename__ = "monitoring_provider_health"
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    freshness_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    completeness_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class ModelHealth(RunArtifact):
    __tablename__ = "monitoring_model_health"
    model_identifier: Mapped[str] = mapped_column(String(96), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class FeatureHealth(RunArtifact):
    __tablename__ = "monitoring_feature_health"
    feature_set_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"), nullable=False)
    completeness_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class CalibrationHealth(RunArtifact):
    __tablename__ = "monitoring_calibration_health"
    calibration_version: Mapped[str | None] = mapped_column(String(161))
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class Alert(RunArtifact):
    __tablename__ = "monitoring_alerts"
    severity: Mapped[AlertSeverity] = mapped_column(SqlEnum(AlertSeverity, name="monitoring_alert_severity"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(96), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class ValidationRecord(RunArtifact):
    __tablename__ = "monitoring_validation_records"
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(SqlEnum(ValidationStatus, name="monitoring_validation_status"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class LineageRecord(RunArtifact):
    __tablename__ = "monitoring_lineage_records"
    artifact_ids: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
