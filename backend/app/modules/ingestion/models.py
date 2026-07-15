"""Persistent audit, identity-link, and transactional-outbox models for ingestion."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
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
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.ingestion.enums import (
    IngestionAuditOutcome,
    IngestionEventType,
    IngestionRunStatus,
    ProviderEntityType,
    RawPayloadStatus,
)
from app.shared.persistence.base import Base


class UUIDPrimaryKeyMixin:
    """Application-assigned UUID identities for distributed ingestion records."""

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Audit timestamps for ingestion entities."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FixtureIngestionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A batch-level operational record for one adapter invocation."""

    __tablename__ = "ingestion_fixture_runs"
    __table_args__ = (
        CheckConstraint("received_count >= 0", name="ck_ingestion_fixture_runs_received_count"),
        CheckConstraint("inserted_count >= 0", name="ck_ingestion_fixture_runs_inserted_count"),
        CheckConstraint("updated_count >= 0", name="ck_ingestion_fixture_runs_updated_count"),
        CheckConstraint("unchanged_count >= 0", name="ck_ingestion_fixture_runs_unchanged_count"),
        CheckConstraint("failed_count >= 0", name="ck_ingestion_fixture_runs_failed_count"),
        Index("ix_ingestion_fixture_runs_provider_started", "provider_name", "started_at"),
    )

    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[IngestionRunStatus] = mapped_column(
        SqlEnum(IngestionRunStatus, name="ingestion_run_status"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_payloads: Mapped[list[RawFixturePayload]] = relationship(back_populates="ingestion_run")
    audit_entries: Mapped[list[FixtureIngestionAudit]] = relationship(
        back_populates="ingestion_run"
    )
    outbox_events: Mapped[list[IngestionOutboxEvent]] = relationship(back_populates="ingestion_run")


class RawFixturePayload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable original fixture JSON retained before normalization and upsert."""

    __tablename__ = "ingestion_raw_fixture_payloads"
    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "idempotency_key",
            name="uq_ingestion_raw_fixture_payloads_provider_key",
        ),
        Index(
            "ix_ingestion_raw_fixture_payloads_provider_fixture",
            "provider_name",
            "provider_fixture_id",
        ),
        Index("ix_ingestion_raw_fixture_payloads_checksum", "checksum"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_fixture_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_fixture_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[RawPayloadStatus] = mapped_column(
        SqlEnum(RawPayloadStatus, name="ingestion_raw_payload_status"), nullable=False, index=True
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

    ingestion_run: Mapped[FixtureIngestionRun] = relationship(back_populates="raw_payloads")
    audit_entries: Mapped[list[FixtureIngestionAudit]] = relationship(back_populates="raw_payload")
    outbox_events: Mapped[list[IngestionOutboxEvent]] = relationship(back_populates="raw_payload")


class FixtureProviderIdentity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stable external fixture identity mapped to exactly one canonical Fixture."""

    __tablename__ = "ingestion_fixture_provider_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "provider_fixture_id",
            name="uq_ingestion_fixture_provider_identities_provider_fixture",
        ),
        Index("ix_ingestion_fixture_provider_identities_fixture", "fixture_id"),
    )

    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_fixture_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fixture_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    latest_raw_payload_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_raw_fixture_payloads.id", ondelete="RESTRICT"),
        nullable=True,
    )
    last_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    latest_raw_payload: Mapped[RawFixturePayload | None] = relationship(
        foreign_keys=[latest_raw_payload_id]
    )


class ProviderEntityIdentity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External identity links for non-fixture canonical entities.

    A generic canonical UUID is intentional: the entity type controls resolution
    while avoiding provider identifiers in Sports Domain tables.
    """

    __tablename__ = "ingestion_provider_entity_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "entity_type",
            "provider_entity_id",
            name="uq_ingestion_provider_entity_identities_provider_entity",
        ),
        Index(
            "ix_ingestion_provider_entity_identities_canonical",
            "entity_type",
            "canonical_entity_id",
        ),
    )

    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[ProviderEntityType] = mapped_column(
        SqlEnum(ProviderEntityType, name="ingestion_provider_entity_type"), nullable=False
    )
    provider_entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_entity_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FixtureIngestionAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only business audit for inserted, updated, unchanged, and invalid payloads."""

    __tablename__ = "ingestion_fixture_audit"
    __table_args__ = (
        Index("ix_ingestion_fixture_audit_provider_occurred", "provider_name", "occurred_at"),
        Index("ix_ingestion_fixture_audit_fixture_occurred", "fixture_id", "occurred_at"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_fixture_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_raw_fixture_payloads.id", ondelete="RESTRICT"),
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
    outcome: Mapped[IngestionAuditOutcome] = mapped_column(
        SqlEnum(IngestionAuditOutcome, name="ingestion_audit_outcome"), nullable=False, index=True
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    changes: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, server_default="{}")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ingestion_run: Mapped[FixtureIngestionRun] = relationship(back_populates="audit_entries")
    raw_payload: Mapped[RawFixturePayload] = relationship(back_populates="audit_entries")


class IngestionOutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Transactional outbox record for reliable downstream fixture event delivery."""

    __tablename__ = "ingestion_outbox_events"
    __table_args__ = (
        UniqueConstraint("event_key", name="uq_ingestion_outbox_events_event_key"),
        Index("ix_ingestion_outbox_events_unpublished", "published_at", "occurred_at"),
    )

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_fixture_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_payload_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_raw_fixture_payloads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[IngestionEventType] = mapped_column(
        SqlEnum(IngestionEventType, name="ingestion_event_type"), nullable=False, index=True
    )
    event_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    ingestion_run: Mapped[FixtureIngestionRun] = relationship(back_populates="outbox_events")
    raw_payload: Mapped[RawFixturePayload] = relationship(back_populates="outbox_events")
