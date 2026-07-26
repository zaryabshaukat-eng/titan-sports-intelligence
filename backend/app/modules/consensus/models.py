"""Append-only Consensus Engine runs, inputs, outputs, lineage, and validation evidence."""

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

from app.modules.consensus.enums import (
    ConsensusRunStatus,
    ConsensusStrategy,
    ConsensusValidationStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ConsensusRun(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One terminal consensus configuration over a compatible set of Probability runs."""

    __tablename__ = "consensus_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_consensus_run_code"),
        UniqueConstraint("idempotency_key", name="uq_consensus_run_idempotency"),
        Index("ix_consensus_runs_dataset_created", "dataset_snapshot_id", "created_at"),
        Index("ix_consensus_runs_strategy_created", "strategy", "created_at"),
    )
    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    strategy: Mapped[ConsensusStrategy] = mapped_column(
        SqlEnum(ConsensusStrategy, name="consensus_strategy"), nullable=False
    )
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ConsensusRunStatus] = mapped_column(
        SqlEnum(ConsensusRunStatus, name="consensus_run_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class ConsensusRunInput(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable record of a Probability run and its model lineage used by consensus."""

    __tablename__ = "consensus_run_inputs"
    __table_args__ = (
        UniqueConstraint(
            "consensus_run_id", "probability_run_id", name="uq_consensus_input_run_probability"
        ),
        Index("ix_consensus_inputs_probability_run", "probability_run_id"),
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    probability_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    model_identifier: Mapped[str] = mapped_column(String(96), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    calibration_version: Mapped[str | None] = mapped_column(String(161))
    research_experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
    )


class ConsensusOutput(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable combined probability plus evidence-only confidence and disagreement metrics."""

    __tablename__ = "consensus_outputs"
    __table_args__ = (
        UniqueConstraint(
            "consensus_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_consensus_output_run_fixture_market_outcome",
        ),
        CheckConstraint(
            "consensus_probability >= 0 AND consensus_probability <= 1",
            name="ck_consensus_output_probability_range",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_consensus_output_confidence_range",
        ),
        CheckConstraint(
            "disagreement_score >= 0 AND disagreement_score <= 1",
            name="ck_consensus_output_disagreement_range",
        ),
        CheckConstraint(
            "contributor_count >= 1 AND expected_count >= contributor_count",
            name="ck_consensus_output_input_counts",
        ),
        Index("ix_consensus_outputs_fixture_market", "fixture_id", "market_type", "outcome"),
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
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
    consensus_probability: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    disagreement_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    agreement_level: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence_metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    disagreement_metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    contributor_count: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ConsensusLineage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "consensus_lineage"
    __table_args__ = (UniqueConstraint("consensus_run_id", name="uq_consensus_lineage_run"),)
    consensus_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    probability_run_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    model_versions: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    calibration_versions: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    research_experiment_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)


class ConsensusValidationRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "consensus_validation_records"
    __table_args__ = (
        UniqueConstraint("consensus_run_id", "rule_name", name="uq_consensus_validation_run_rule"),
        Index("ix_consensus_validation_run", "consensus_run_id"),
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ConsensusValidationStatus] = mapped_column(
        SqlEnum(ConsensusValidationStatus, name="consensus_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
