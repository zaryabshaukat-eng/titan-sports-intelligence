from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.evaluation.enums import BacktestRunStatus, BacktestValidationStatus, ScenarioType
from app.shared.persistence.base import Base


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BacktestRun(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_backtest_run_code"),
        UniqueConstraint("idempotency_key", name="uq_backtest_run_idempotency"),
        Index("ix_backtest_runs_dataset_created", "dataset_snapshot_id", "created_at"),
    )
    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    research_experiment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    probability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    explainability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explainability_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scenario: Mapped[ScenarioType] = mapped_column(
        SqlEnum(ScenarioType, name="backtest_scenario"), nullable=False
    )
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BacktestRunStatus] = mapped_column(
        SqlEnum(BacktestRunStatus, name="backtest_run_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class BacktestResult(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "backtest_results"
    __table_args__ = (
        UniqueConstraint(
            "backtest_run_id", "probability_output_id", name="uq_backtest_result_run_output"
        ),
        Index("ix_backtest_results_fixture", "fixture_id"),
    )
    backtest_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("backtest_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    probability_output_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("probability_outputs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sports_fixtures.id", ondelete="RESTRICT"), nullable=False
    )
    market_type: Mapped[str] = mapped_column(String(96), nullable=False)
    outcome: Mapped[str] = mapped_column(String(96), nullable=False)
    predicted_probability: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    observed_outcome: Mapped[bool] = mapped_column(nullable=False)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fixture_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestMetric(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "backtest_metrics"
    __table_args__ = (UniqueConstraint("backtest_run_id", name="uq_backtest_metric_run"),)
    backtest_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="RESTRICT"), nullable=False
    )
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    reliability: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)


class BacktestLineage(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "backtest_lineage"
    __table_args__ = (UniqueConstraint("backtest_run_id", name="uq_backtest_lineage_run"),)
    backtest_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="RESTRICT"), nullable=False
    )
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_ids: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)


class BacktestValidationRecord(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "backtest_validation_records"
    __table_args__ = (
        UniqueConstraint("backtest_run_id", "rule_name", name="uq_backtest_validation_run_rule"),
        Index("ix_backtest_validation_run", "backtest_run_id"),
    )
    backtest_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="RESTRICT"), nullable=False
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[BacktestValidationStatus] = mapped_column(
        SqlEnum(BacktestValidationStatus, name="backtest_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
