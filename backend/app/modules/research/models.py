"""Append-only Research Engine records, immutable dataset materializations, and evidence lineage."""

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

from app.modules.research.enums import (
    AnalysisType,
    ExperimentStatus,
    HypothesisDecision,
    ValidationStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Use UUIDs for durable research artifacts and reproducibility references."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedAtMixin:
    """Append-only records retain only creation time; migration prohibits mutation."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DatasetSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A frozen, materialized selection of Feature Store values used by experiments."""

    __tablename__ = "research_dataset_snapshots"
    __table_args__ = (
        UniqueConstraint("dataset_code", "version", name="uq_research_dataset_code_version"),
        UniqueConstraint("idempotency_key", name="uq_research_dataset_idempotency"),
        CheckConstraint("source_value_count >= 0", name="ck_research_dataset_source_value_count"),
        Index("ix_research_datasets_feature_set_created", "feature_set_version_id", "created_at"),
    )

    dataset_code: Mapped[str] = mapped_column(String(96), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selection: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    generator_versions: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    source_value_count: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class DatasetSnapshotRow(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Materialized Feature Store values; experiments never query live feature rows."""

    __tablename__ = "research_dataset_snapshot_rows"
    __table_args__ = (
        UniqueConstraint(
            "dataset_snapshot_id",
            "source_feature_value_id",
            name="uq_research_dataset_source_value",
        ),
        Index("ix_research_dataset_rows_snapshot_feature", "dataset_snapshot_id", "feature_id"),
        Index("ix_research_dataset_rows_snapshot_fixture", "dataset_snapshot_id", "fixture_id"),
        Index("ix_research_dataset_rows_snapshot_team", "dataset_snapshot_id", "team_id"),
    )

    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_feature_value_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_values.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_definition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fixture_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_fixtures.id", ondelete="RESTRICT")
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_teams.id", ondelete="RESTRICT")
    )
    player_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("statistics_players.id", ondelete="RESTRICT")
    )
    competition_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_competitions.id", ondelete="RESTRICT")
    )
    season_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_seasons.id", ondelete="RESTRICT")
    )
    value: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchExperiment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable terminal experiment and its reproducibility configuration."""

    __tablename__ = "research_experiments"
    __table_args__ = (
        UniqueConstraint("experiment_code", name="uq_research_experiment_code"),
        UniqueConstraint("idempotency_key", name="uq_research_experiment_idempotency"),
        Index("ix_research_experiments_dataset_created", "dataset_snapshot_id", "created_at"),
        Index(
            "ix_research_experiments_feature_set_created", "feature_set_version_id", "created_at"
        ),
    )

    experiment_code: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
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
    generator_versions: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        SqlEnum(ExperimentStatus, name="research_experiment_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class ExperimentStatisticResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One immutable descriptive, correlation, distribution, or significance result."""

    __tablename__ = "research_experiment_statistic_results"
    __table_args__ = (
        UniqueConstraint("experiment_id", "result_key", name="uq_research_experiment_result_key"),
        CheckConstraint("sample_size >= 0", name="ck_research_result_sample_size"),
        Index("ix_research_results_experiment_analysis", "experiment_id", "analysis_type"),
    )

    experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    result_key: Mapped[str] = mapped_column(String(160), nullable=False)
    analysis_type: Mapped[AnalysisType] = mapped_column(
        SqlEnum(AnalysisType, name="research_analysis_type"), nullable=False
    )
    feature_id: Mapped[str] = mapped_column(String(128), nullable=False)
    related_feature_id: Mapped[str | None] = mapped_column(String(128))
    method: Mapped[str] = mapped_column(String(96), nullable=False)
    values: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_interval_low: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    confidence_interval_high: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    p_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))


class ResearchHypothesis(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable hypothesis statement reusable across several experiments."""

    __tablename__ = "research_hypotheses"
    __table_args__ = (UniqueConstraint("hypothesis_code", name="uq_research_hypothesis_code"),)

    hypothesis_code: Mapped[str] = mapped_column(String(96), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)


class HypothesisEvaluation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only hypothesis conclusion with immutable experiment evidence."""

    __tablename__ = "research_hypothesis_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "hypothesis_id", "experiment_id", name="uq_research_hypothesis_experiment"
        ),
        CheckConstraint(
            "p_value IS NULL OR (p_value >= 0 AND p_value <= 1)",
            name="ck_research_hypothesis_p_value",
        ),
        Index("ix_research_hypothesis_evaluations_experiment", "experiment_id"),
    )

    hypothesis_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_hypotheses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    statistic_result_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiment_statistic_results.id", ondelete="RESTRICT"),
    )
    result: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    statistical_significance: Mapped[bool | None] = mapped_column()
    p_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    decision: Mapped[HypothesisDecision] = mapped_column(
        SqlEnum(HypothesisDecision, name="research_hypothesis_decision"), nullable=False
    )


class ExperimentLineage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Explicit experiment-to-dataset/version/parameter lineage for research auditability."""

    __tablename__ = "research_experiment_lineage"
    __table_args__ = (UniqueConstraint("experiment_id", name="uq_research_experiment_lineage"),)

    experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
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
    generator_versions: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)


class ExperimentValidationRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Persisted validation evidence, including failed immutable experiment attempts."""

    __tablename__ = "research_experiment_validation_records"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id", "rule_name", name="uq_research_experiment_validation_rule"
        ),
        Index("ix_research_validation_experiment", "experiment_id"),
    )

    experiment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(
        SqlEnum(ValidationStatus, name="research_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
