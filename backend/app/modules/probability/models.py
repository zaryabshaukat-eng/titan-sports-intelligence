"""Append-only Probability Engine records, calibrated outputs, evaluation, and lineage."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
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
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.probability.enums import (
    CalibrationMethod,
    ProbabilityRunStatus,
    ProbabilityValidationStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Use UUID identities for durable probability evidence references."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedAtMixin:
    """Append-only probability artifacts retain only their creation time."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CalibrationVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned immutable calibration parameters and declared model compatibility."""

    __tablename__ = "probability_calibration_versions"
    __table_args__ = (
        UniqueConstraint(
            "calibration_code", "version", name="uq_probability_calibration_code_version"
        ),
        UniqueConstraint("idempotency_key", name="uq_probability_calibration_idempotency"),
        Index("ix_probability_calibration_method_created", "method", "created_at"),
    )

    calibration_code: Mapped[str] = mapped_column(String(96), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    method: Mapped[CalibrationMethod] = mapped_column(
        SqlEnum(CalibrationMethod, name="probability_calibration_method"), nullable=False
    )
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    compatible_model_identifiers: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class ProbabilityRun(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable configuration and status for one deterministic probability computation."""

    __tablename__ = "probability_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_probability_run_code"),
        UniqueConstraint("idempotency_key", name="uq_probability_run_idempotency"),
        Index("ix_probability_runs_dataset_created", "dataset_snapshot_id", "created_at"),
        Index("ix_probability_runs_experiment_created", "research_experiment_id", "created_at"),
        Index(
            "ix_probability_runs_model_created",
            "model_identifier",
            "model_version",
            "created_at",
        ),
    )

    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    research_experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_identifier: Mapped[str] = mapped_column(String(96), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    calibration_version_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_calibration_versions.id", ondelete="RESTRICT"),
    )
    market_type: Mapped[str] = mapped_column(String(96), nullable=False)
    outcome: Mapped[str] = mapped_column(String(96), nullable=False)
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ProbabilityRunStatus] = mapped_column(
        SqlEnum(ProbabilityRunStatus, name="probability_run_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class ProbabilityOutput(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One immutable fixture/outcome estimate emitted by a completed probability run."""

    __tablename__ = "probability_outputs"
    __table_args__ = (
        UniqueConstraint(
            "probability_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_probability_output_run_fixture_market_outcome",
        ),
        CheckConstraint(
            "estimated_probability >= 0 AND estimated_probability <= 1",
            name="ck_probability_output_probability_range",
        ),
        CheckConstraint(
            "confidence_interval_low >= 0 AND confidence_interval_high <= 1",
            name="ck_probability_output_confidence_range",
        ),
        CheckConstraint(
            "confidence_interval_low <= estimated_probability "
            "AND estimated_probability <= confidence_interval_high",
            name="ck_probability_output_confidence_contains_estimate",
        ),
        CheckConstraint("support_count >= 1", name="ck_probability_output_support_count"),
        Index(
            "ix_probability_outputs_fixture_market_prediction",
            "fixture_id",
            "market_type",
            "prediction_timestamp",
        ),
    )

    probability_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_type: Mapped[str] = mapped_column(String(96), nullable=False)
    outcome: Mapped[str] = mapped_column(String(96), nullable=False)
    estimated_probability: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    confidence_interval_low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    confidence_interval_high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    calibration_version: Mapped[str | None] = mapped_column(String(161))
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    support_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ProbabilityEvaluation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable evaluation metrics computed from a known run's output/observation pairs."""

    __tablename__ = "probability_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "probability_run_id", "evaluation_code", name="uq_probability_evaluation_run_code"
        ),
        UniqueConstraint("idempotency_key", name="uq_probability_evaluation_idempotency"),
        CheckConstraint("sample_count >= 1", name="ck_probability_evaluation_sample_count"),
        Index("ix_probability_evaluations_run_created", "probability_run_id", "created_at"),
    )

    probability_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    evaluation_code: Mapped[str] = mapped_column(String(96), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    reliability: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class ProbabilityLineage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Full immutable replay path for a ProbabilityRun and its calibration choice."""

    __tablename__ = "probability_lineage"
    __table_args__ = (UniqueConstraint("probability_run_id", name="uq_probability_lineage_run"),)

    probability_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    research_experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    model_identifier: Mapped[str] = mapped_column(String(96), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    calibration_version: Mapped[str | None] = mapped_column(String(161))
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)


class ProbabilityValidationRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Persisted validation evidence for both completed and rejected probability runs."""

    __tablename__ = "probability_validation_records"
    __table_args__ = (
        UniqueConstraint(
            "probability_run_id", "rule_name", name="uq_probability_validation_run_rule"
        ),
        Index("ix_probability_validation_run", "probability_run_id"),
    )

    probability_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ProbabilityValidationStatus] = mapped_column(
        SqlEnum(ProbabilityValidationStatus, name="probability_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
