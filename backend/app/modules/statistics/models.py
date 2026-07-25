"""Provider-neutral statistic definitions, immutable observations, provenance, and outbox models."""
# ruff: noqa: E501, E701, E702

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.statistics.enums import (
    RawStatisticPayloadStatus,
    StatisticMappingEntityType,
    StatisticsAuditOutcome,
    StatisticScope,
    StatisticsEventType,
    StatisticsRunStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class StatisticProvider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_providers"
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class StatisticCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_categories"
    code: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    value_schema: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class StatisticVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_versions"
    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "category_id",
            "version",
            name="uq_statistics_versions_provider_category_version",
        ),
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")


class FixtureStatistic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_fixture_statistics"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id", "category_id", "version_id", name="uq_statistics_fixture_series"
        ),
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )


class TeamStatistic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_team_statistics"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id", "team_id", "category_id", "version_id", name="uq_statistics_team_series"
        ),
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )


class StatisticPlayer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical player identity owned here until a dedicated athlete domain exists."""

    __tablename__ = "statistics_players"
    __table_args__ = (
        UniqueConstraint("name", "birth_date", name="uq_statistics_players_name_birth_date"),
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    birth_date: Mapped[str | None] = mapped_column(String(10))
    nationality: Mapped[str | None] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class PlayerStatistic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_player_statistics"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "player_id",
            "category_id",
            "version_id",
            name="uq_statistics_player_series",
        ),
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_players.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_teams.id", ondelete="RESTRICT")
    )
    category_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )


class StatisticIngestionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_ingestion_runs"
    __table_args__ = (
        CheckConstraint("received_count >= 0", name="ck_statistics_runs_received_count"),
        CheckConstraint("snapshots_created_count >= 0", name="ck_statistics_runs_created_count"),
        CheckConstraint("failed_count >= 0", name="ck_statistics_runs_failed_count"),
        Index("ix_statistics_runs_provider_started", "provider_id", "started_at"),
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[StatisticsRunStatus] = mapped_column(
        SqlEnum(StatisticsRunStatus, name="statistics_run_status"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    snapshots_created_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class RawStatisticPayload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_raw_payloads"
    __table_args__ = (
        UniqueConstraint("provider_id", "idempotency_key", name="uq_statistics_raw_provider_key"),
        Index("ix_statistics_raw_checksum", "checksum"),
        Index("ix_statistics_raw_ingestion_run", "ingestion_run_id"),
        Index("ix_statistics_raw_fixture", "canonical_fixture_id"),
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_fixture_id: Mapped[str | None] = mapped_column(String(128))
    fixture_provider_name: Mapped[str | None] = mapped_column(String(64))
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[RawStatisticPayloadStatus] = mapped_column(
        SqlEnum(RawStatisticPayloadStatus, name="statistics_raw_payload_status"), nullable=False
    )
    validation_errors: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB)
    canonical_fixture_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("sports_fixtures.id", ondelete="RESTRICT")
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StatisticProviderMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_provider_mappings"
    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "entity_type",
            "provider_entity_id",
            name="uq_statistics_provider_mapping",
        ),
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entity_type: Mapped[StatisticMappingEntityType] = mapped_column(
        SqlEnum(StatisticMappingEntityType, name="statistics_mapping_entity_type"), nullable=False
    )
    provider_entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_entity_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False, index=True
    )


class StatisticSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_snapshots"
    __table_args__ = (
        CheckConstraint(
            "(fixture_statistic_id IS NOT NULL)::int + (team_statistic_id IS NOT NULL)::int + (player_statistic_id IS NOT NULL)::int = 1",
            name="ck_statistics_snapshot_one_series",
        ),
        UniqueConstraint(
            "provider_id",
            "scope",
            "series_id",
            "observed_at",
            "checksum",
            name="uq_statistics_snapshot_observation",
        ),
        Index("ix_statistics_snapshots_fixture_observed", "fixture_id", "observed_at"),
        Index(
            "ix_statistics_snapshots_series_latest",
            "series_id",
            "observed_at",
            "created_at",
        ),
        Index("ix_statistics_snapshots_ingestion_run", "ingestion_run_id"),
        Index("ix_statistics_snapshots_raw_payload", "raw_payload_id"),
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scope: Mapped[StatisticScope] = mapped_column(
        SqlEnum(StatisticScope, name="statistics_scope"), nullable=False
    )
    series_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False, index=True
    )
    fixture_statistic_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_fixture_statistics.id", ondelete="RESTRICT"),
    )
    team_statistic_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_team_statistics.id", ondelete="RESTRICT"),
    )
    player_statistic_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_player_statistics.id", ondelete="RESTRICT"),
    )
    values: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)


class StatisticAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_audits"
    __table_args__ = (
        Index("ix_statistics_audits_ingestion_run", "ingestion_run_id"),
        Index("ix_statistics_audits_raw_payload", "raw_payload_id"),
        Index("ix_statistics_audits_provider_created", "provider_id", "created_at"),
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome: Mapped[StatisticsAuditOutcome] = mapped_column(
        SqlEnum(StatisticsAuditOutcome, name="statistics_audit_outcome"), nullable=False
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    changes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    error_details: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB)


class StatisticsOutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statistics_outbox_events"
    __table_args__ = (
        UniqueConstraint("event_type", "event_key", name="uq_statistics_outbox_event"),
        Index("ix_statistics_outbox_ingestion_run", "ingestion_run_id"),
        Index("ix_statistics_outbox_raw_payload", "raw_payload_id"),
        Index("ix_statistics_outbox_unpublished", "published_at", "created_at"),
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[StatisticsEventType] = mapped_column(
        SqlEnum(StatisticsEventType, name="statistics_event_type"), nullable=False
    )
    event_key: Mapped[str] = mapped_column(String(192), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    lease_owner: Mapped[str | None] = mapped_column(String(96), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
