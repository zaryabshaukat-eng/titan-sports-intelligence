"""Feature Store metadata and append-only feature-value persistence models."""

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
    text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.feature_store.enums import (
    FeatureDataType,
    FeatureType,
    GenerationStatus,
    MissingValuePolicy,
    ValidationStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Use UUID identities so feature evidence can be shared safely across services."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedAtMixin:
    """Append-only records expose their creation time but are never updated in place."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FeatureSet(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Stable named grouping for independently versioned feature definitions."""

    __tablename__ = "feature_store_feature_sets"

    code: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)


class FeatureSetVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable registry snapshot selected by all generation and future training work."""

    __tablename__ = "feature_store_feature_set_versions"
    __table_args__ = (
        UniqueConstraint("feature_set_id", "version", name="uq_feature_store_set_version"),
        Index("ix_feature_store_set_versions_set_created", "feature_set_id", "created_at"),
    )

    feature_set_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_sets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    source_modules: Mapped[list[str]] = mapped_column(JSONB, nullable=False)


class FeatureDefinition(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable specification for one feature in one feature-set version."""

    __tablename__ = "feature_store_feature_definitions"
    __table_args__ = (
        UniqueConstraint(
            "feature_set_version_id", "feature_id", name="uq_feature_store_definition_feature_id"
        ),
        Index("ix_feature_store_definitions_set_type", "feature_set_version_id", "feature_type"),
    )

    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    source_modules: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    calculation_logic: Mapped[str] = mapped_column(Text, nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SqlEnum(FeatureType, name="feature_store_feature_type"), nullable=False
    )
    data_type: Mapped[FeatureDataType] = mapped_column(
        SqlEnum(FeatureDataType, name="feature_store_data_type"), nullable=False
    )
    missing_value_policy: Mapped[MissingValuePolicy] = mapped_column(
        SqlEnum(MissingValuePolicy, name="feature_store_missing_value_policy"), nullable=False
    )
    validity_window_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FeatureGenerationRun(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Durable, retry-safe record of a deterministic feature regeneration request."""

    __tablename__ = "feature_store_generation_runs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_feature_store_generation_idempotency"),
        CheckConstraint("generated_count >= 0", name="ck_feature_store_generation_generated_count"),
        Index("ix_feature_store_generation_fixture_asof", "fixture_id", "as_of"),
        Index("ix_feature_store_generation_set_status", "feature_set_version_id", "status"),
    )

    feature_set_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        SqlEnum(GenerationStatus, name="feature_store_generation_status"), nullable=False
    )
    generated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeatureValue(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """An immutable feature value; corrections are represented by a later generation run."""

    __tablename__ = "feature_store_feature_values"
    __table_args__ = (
        UniqueConstraint(
            "generation_run_id", "feature_definition_id", name="uq_feature_store_run_definition"
        ),
        CheckConstraint(
            "(fixture_id IS NOT NULL)::int + (team_id IS NOT NULL)::int + "
            "(player_id IS NOT NULL)::int + (competition_id IS NOT NULL)::int + "
            "(season_id IS NOT NULL)::int >= 1",
            name="ck_feature_store_value_has_subject",
        ),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 1", name="ck_feature_store_value_quality"
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_feature_store_value_validity_window",
        ),
        Index(
            "ix_feature_store_values_fixture_definition_observed",
            "fixture_id",
            "feature_definition_id",
            text("observed_at DESC"),
        ),
        Index("ix_feature_store_values_team_observed", "team_id", text("observed_at DESC")),
        Index("ix_feature_store_values_player_observed", "player_id", text("observed_at DESC")),
        Index(
            "ix_feature_store_values_competition_observed",
            "competition_id",
            text("observed_at DESC"),
        ),
        Index("ix_feature_store_values_season_observed", "season_id", text("observed_at DESC")),
    )

    generation_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_generation_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_definition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
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
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeatureLineage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable source-to-feature evidence; sources never include raw provider payloads."""

    __tablename__ = "feature_store_lineage"
    __table_args__ = (
        UniqueConstraint(
            "feature_value_id",
            "source_module",
            "source_entity_type",
            "source_record_id",
            name="uq_feature_store_lineage_source",
        ),
        Index("ix_feature_store_lineage_feature", "feature_value_id"),
        Index("ix_feature_store_lineage_source", "source_module", "source_record_id"),
    )

    feature_value_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_values.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_module: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(96), nullable=False)
    source_record_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    source_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_fingerprint: Mapped[str | None] = mapped_column(String(64))
    calculation_logic: Mapped[str] = mapped_column(Text, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(64), nullable=False)


class FeatureValidationRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only evidence of each null, range, temporal, and dependency check."""

    __tablename__ = "feature_store_validation_records"
    __table_args__ = (
        UniqueConstraint(
            "generation_run_id",
            "feature_definition_id",
            "rule_name",
            name="uq_feature_store_validation_rule",
        ),
        Index("ix_feature_store_validation_run", "generation_run_id"),
    )

    generation_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_generation_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_definition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_definitions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_value_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("feature_store_feature_values.id", ondelete="RESTRICT"),
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(
        SqlEnum(ValidationStatus, name="feature_store_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
