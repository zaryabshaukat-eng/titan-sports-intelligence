"""Canonical market-data, immutable odds-history, audit, identity, and outbox models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.market_data.enums import (
    MarketDataEventType,
    MarketProviderEntityType,
    OddsAuditOutcome,
    OddsIngestionRunStatus,
    OddsMovementType,
    RawOddsPayloadStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Application-assigned UUID identities for market-data records."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Created and updated timestamps shared by Market Data records."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Bookmaker(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical bookmaker, kept independent of any provider's identifiers."""

    __tablename__ = "market_data_bookmakers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_market_data_bookmakers_name"),
        UniqueConstraint("code", name="uq_market_data_bookmakers_code"),
        Index("ix_market_data_bookmakers_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    odds_snapshots: Mapped[list[OddsSnapshot]] = relationship(back_populates="bookmaker")


class MarketType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Extensible canonical market taxonomy, including configurable parameters for future types."""

    __tablename__ = "market_data_market_types"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameter_schema: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    markets: Mapped[list[Market]] = relationship(back_populates="market_type")


class MarketStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Configurable canonical lifecycle status for a fixture market."""

    __tablename__ = "market_data_market_statuses"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_market_data_market_statuses_sort_order"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    markets: Mapped[list[Market]] = relationship(back_populates="market_status")


class Market(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A canonical market for one fixture, type, period, and optional numerical line."""

    __tablename__ = "market_data_markets"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "market_type_id",
            "period_code",
            "line_key",
            name="uq_market_data_markets_fixture_type_period_line",
        ),
        CheckConstraint("char_length(period_code) >= 1", name="ck_market_data_markets_period_code"),
        Index("ix_market_data_markets_fixture_status", "fixture_id", "market_status_id"),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_type_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_market_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_status_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_market_statuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period_code: Mapped[str] = mapped_column(String(32), nullable=False, server_default="full_time")
    line_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    line_key: Mapped[str] = mapped_column(String(32), nullable=False, server_default="none")
    attributes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    status_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    market_type: Mapped[MarketType] = relationship(back_populates="markets")
    market_status: Mapped[MarketStatus] = relationship(back_populates="markets")
    selections: Mapped[list[Selection]] = relationship(back_populates="market")
    odds_snapshots: Mapped[list[OddsSnapshot]] = relationship(back_populates="market")
    movements: Mapped[list[OddsMovement]] = relationship(back_populates="market")


class Selection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A durable market outcome; lifecycle fields preserve removed selections for replay."""

    __tablename__ = "market_data_selections"
    __table_args__ = (
        UniqueConstraint("market_id", "selection_key", name="uq_market_data_selections_market_key"),
        Index("ix_market_data_selections_market_active", "market_id", "is_active"),
    )

    market_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_markets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selection_key: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attributes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")

    market: Mapped[Market] = relationship(back_populates="selections")
    odds_snapshots: Mapped[list[OddsSnapshot]] = relationship(back_populates="selection")
    movements: Mapped[list[OddsMovement]] = relationship(back_populates="selection")


class OddsIngestionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Batch-level operational record for one odds-provider import."""

    __tablename__ = "market_data_odds_ingestion_runs"
    __table_args__ = (
        CheckConstraint("received_count >= 0", name="ck_market_data_odds_runs_received_count"),
        CheckConstraint(
            "snapshots_created_count >= 0", name="ck_market_data_odds_runs_created_count"
        ),
        CheckConstraint(
            "snapshots_ignored_count >= 0", name="ck_market_data_odds_runs_ignored_count"
        ),
        CheckConstraint("movements_count >= 0", name="ck_market_data_odds_runs_movements_count"),
        CheckConstraint("failed_count >= 0", name="ck_market_data_odds_runs_failed_count"),
        Index("ix_market_data_odds_runs_provider_started", "provider_name", "started_at"),
    )

    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[OddsIngestionRunStatus] = mapped_column(
        SqlEnum(OddsIngestionRunStatus, name="market_data_odds_ingestion_run_status"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    snapshots_created_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    snapshots_ignored_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    movements_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_payloads: Mapped[list[RawOddsPayload]] = relationship(back_populates="ingestion_run")
    audit_entries: Mapped[list[OddsAudit]] = relationship(back_populates="ingestion_run")
    snapshots: Mapped[list[OddsSnapshot]] = relationship(back_populates="ingestion_run")
    outbox_events: Mapped[list[MarketDataOutboxEvent]] = relationship(back_populates="ingestion_run")


class RawOddsPayload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable raw provider JSON receipt retained before any normalization or market mutation."""

    __tablename__ = "market_data_raw_odds_payloads"
    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "idempotency_key",
            name="uq_market_data_raw_odds_payloads_provider_key",
        ),
        Index("ix_market_data_raw_odds_payloads_provider_fixture", "provider_name", "provider_fixture_id"),
        Index("ix_market_data_raw_odds_payloads_checksum", "checksum"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fixture_provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_fixture_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[RawOddsPayloadStatus] = mapped_column(
        SqlEnum(RawOddsPayloadStatus, name="market_data_raw_odds_payload_status"),
        nullable=False,
        index=True,
    )
    validation_errors: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canonical_fixture_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    ingestion_run: Mapped[OddsIngestionRun] = relationship(back_populates="raw_payloads")
    audit_entries: Mapped[list[OddsAudit]] = relationship(back_populates="raw_payload")
    snapshots: Mapped[list[OddsSnapshot]] = relationship(back_populates="raw_payload")
    outbox_events: Mapped[list[MarketDataOutboxEvent]] = relationship(back_populates="raw_payload")


class MarketProviderMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Provider-neutral external-to-canonical mapping for fixtures, bookmakers, markets, and selections."""

    __tablename__ = "market_data_provider_mappings"
    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "entity_type",
            "provider_entity_id",
            name="uq_market_data_provider_mappings_provider_entity",
        ),
        Index(
            "ix_market_data_provider_mappings_canonical",
            "entity_type",
            "canonical_entity_id",
        ),
    )

    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[MarketProviderEntityType] = mapped_column(
        SqlEnum(MarketProviderEntityType, name="market_data_provider_entity_type"), nullable=False
    )
    provider_entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_entity_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OddsSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only decimal-odds observation with complete provider and raw-payload provenance."""

    __tablename__ = "market_data_odds_snapshots"
    __table_args__ = (
        CheckConstraint("decimal_odds > 1", name="ck_market_data_odds_snapshots_decimal_odds"),
        CheckConstraint(
            "implied_probability > 0 AND implied_probability < 1",
            name="ck_market_data_odds_snapshots_implied_probability",
        ),
        UniqueConstraint(
            "provider_name",
            "bookmaker_id",
            "selection_id",
            "observed_at",
            "checksum",
            name="uq_market_data_odds_snapshots_observation",
        ),
        Index(
            "ix_market_data_odds_snapshots_selection_observed",
            "selection_id",
            "observed_at",
        ),
        Index(
            "ix_market_data_odds_snapshots_fixture_market_observed",
            "fixture_id",
            "market_id",
            "observed_at",
        ),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_raw_odds_payloads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    bookmaker_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_bookmakers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_markets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selection_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_selections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decimal_odds: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    implied_probability: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    ingestion_run: Mapped[OddsIngestionRun] = relationship(back_populates="snapshots")
    raw_payload: Mapped[RawOddsPayload] = relationship(back_populates="snapshots")
    bookmaker: Mapped[Bookmaker] = relationship(back_populates="odds_snapshots")
    market: Mapped[Market] = relationship(back_populates="odds_snapshots")
    selection: Mapped[Selection] = relationship(back_populates="odds_snapshots")
    previous_for_movements: Mapped[list[OddsMovement]] = relationship(
        back_populates="previous_snapshot", foreign_keys="OddsMovement.previous_snapshot_id"
    )
    current_for_movements: Mapped[list[OddsMovement]] = relationship(
        back_populates="current_snapshot", foreign_keys="OddsMovement.current_snapshot_id"
    )


class OddsMovement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only detection record for price, market-status, and selection-lifecycle changes."""

    __tablename__ = "market_data_odds_movements"
    __table_args__ = (
        Index("ix_market_data_odds_movements_market_observed", "market_id", "observed_at"),
        Index("ix_market_data_odds_movements_selection_observed", "selection_id", "observed_at"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_raw_odds_payloads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bookmaker_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_bookmakers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_markets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selection_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_selections.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    previous_snapshot_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
    )
    current_snapshot_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
    )
    movement_type: Mapped[OddsMovementType] = mapped_column(
        SqlEnum(OddsMovementType, name="market_data_odds_movement_type"),
        nullable=False,
        index=True,
    )
    previous_decimal_odds: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    current_decimal_odds: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    delta_decimal_odds: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    details: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")

    market: Mapped[Market] = relationship(back_populates="movements")
    selection: Mapped[Selection | None] = relationship(back_populates="movements")
    previous_snapshot: Mapped[OddsSnapshot | None] = relationship(
        back_populates="previous_for_movements", foreign_keys=[previous_snapshot_id]
    )
    current_snapshot: Mapped[OddsSnapshot | None] = relationship(
        back_populates="current_for_movements", foreign_keys=[current_snapshot_id]
    )


class OddsAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only audit of validation, ignored prices, snapshots, and movements for each raw payload."""

    __tablename__ = "market_data_odds_audit"
    __table_args__ = (
        Index("ix_market_data_odds_audit_provider_occurred", "provider_name", "occurred_at"),
        Index("ix_market_data_odds_audit_fixture_occurred", "fixture_id", "occurred_at"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_raw_odds_payloads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_fixture_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[OddsAuditOutcome] = mapped_column(
        SqlEnum(OddsAuditOutcome, name="market_data_odds_audit_outcome"),
        nullable=False,
        index=True,
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    changes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    snapshots_created: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    snapshots_ignored: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    movements_detected: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ingestion_run: Mapped[OddsIngestionRun] = relationship(back_populates="audit_entries")
    raw_payload: Mapped[RawOddsPayload] = relationship(back_populates="audit_entries")


class MarketDataOutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Transactional-outbox record for reliable future Market Data event delivery."""

    __tablename__ = "market_data_outbox_events"
    __table_args__ = (
        UniqueConstraint("event_key", name="uq_market_data_outbox_events_event_key"),
        Index("ix_market_data_outbox_events_unpublished", "published_at", "occurred_at"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_odds_ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("market_data_raw_odds_payloads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[MarketDataEventType] = mapped_column(
        SqlEnum(MarketDataEventType, name="market_data_event_type"), nullable=False, index=True
    )
    event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    ingestion_run: Mapped[OddsIngestionRun] = relationship(back_populates="outbox_events")
    raw_payload: Mapped[RawOddsPayload] = relationship(back_populates="outbox_events")
