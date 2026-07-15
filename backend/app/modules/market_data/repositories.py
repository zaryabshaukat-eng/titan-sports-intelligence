"""Async persistence repositories for immutable market-data ingestion records."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.market_data.enums import (
    MarketDataEventType,
    MarketProviderEntityType,
    OddsAuditOutcome,
    OddsIngestionRunStatus,
    OddsMovementType,
    RawOddsPayloadStatus,
)
from app.modules.market_data.models import (
    MarketDataOutboxEvent,
    MarketProviderMapping,
    OddsAudit,
    OddsIngestionRun,
    OddsMovement,
    OddsSnapshot,
    RawOddsPayload,
    Selection,
)


class MarketDataIngestionRepository:
    """Persist Market Data provenance, mappings, immutable snapshots, and outbox events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, provider_name: str, received_count: int) -> OddsIngestionRun:
        """Create and flush one auditable batch-level market-data run."""
        run = OddsIngestionRun(
            provider_name=provider_name,
            status=OddsIngestionRunStatus.RUNNING,
            received_count=received_count,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_raw_payload_by_idempotency_key(
        self, provider_name: str, idempotency_key: str
    ) -> RawOddsPayload | None:
        """Return the immutable original receipt for a retry-safe provider payload key."""
        statement = select(RawOddsPayload).where(
            RawOddsPayload.provider_name == provider_name,
            RawOddsPayload.idempotency_key == idempotency_key,
        )
        return await self.session.scalar(statement)

    async def create_raw_payload_once(
        self,
        *,
        run: OddsIngestionRun,
        provider_name: str,
        fixture_provider_name: str | None,
        provider_fixture_id: str | None,
        checksum: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> tuple[RawOddsPayload, bool]:
        """Persist raw JSON once, including safe handling of concurrent retry insert races."""
        existing = await self.get_raw_payload_by_idempotency_key(provider_name, idempotency_key)
        if existing is not None:
            return existing, False

        raw_payload = RawOddsPayload(
            ingestion_run_id=run.id,
            provider_name=provider_name,
            fixture_provider_name=fixture_provider_name,
            provider_fixture_id=provider_fixture_id,
            checksum=checksum,
            idempotency_key=idempotency_key,
            payload=payload,
            validation_status=RawOddsPayloadStatus.RECEIVED,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(raw_payload)
                await self.session.flush()
        except IntegrityError:
            existing = await self.get_raw_payload_by_idempotency_key(provider_name, idempotency_key)
            if existing is None:
                raise
            return existing, False
        return raw_payload, True

    async def get_mapping(
        self,
        provider_name: str,
        entity_type: MarketProviderEntityType,
        provider_entity_id: str,
    ) -> MarketProviderMapping | None:
        """Find an external-to-canonical identity mapping by provider-controlled identity."""
        statement = select(MarketProviderMapping).where(
            MarketProviderMapping.provider_name == provider_name,
            MarketProviderMapping.entity_type == entity_type,
            MarketProviderMapping.provider_entity_id == provider_entity_id,
        )
        return await self.session.scalar(statement)

    async def link_mapping(
        self,
        *,
        provider_name: str,
        entity_type: MarketProviderEntityType,
        provider_entity_id: str,
        canonical_entity_id: UUID,
    ) -> tuple[MarketProviderMapping, bool]:
        """Persist one stable external identity mapping and reactivate known returned selections."""
        existing = await self.get_mapping(provider_name, entity_type, provider_entity_id)
        if existing is not None:
            existing.last_seen_at = datetime.now(UTC)
            existing.is_active = True
            existing.removed_at = None
            return existing, False

        mapping = MarketProviderMapping(
            provider_name=provider_name,
            entity_type=entity_type,
            provider_entity_id=provider_entity_id,
            canonical_entity_id=canonical_entity_id,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(mapping)
                await self.session.flush()
        except IntegrityError:
            existing = await self.get_mapping(provider_name, entity_type, provider_entity_id)
            if existing is None:
                raise
            existing.last_seen_at = datetime.now(UTC)
            existing.is_active = True
            existing.removed_at = None
            return existing, False
        return mapping, True

    async def active_selection_mappings_for_market(
        self, provider_name: str, market_id: UUID
    ) -> list[MarketProviderMapping]:
        """List active source selection mappings for one provider-owned market view."""
        statement = (
            select(MarketProviderMapping)
            .join(Selection, Selection.id == MarketProviderMapping.canonical_entity_id)
            .where(
                MarketProviderMapping.provider_name == provider_name,
                MarketProviderMapping.entity_type == MarketProviderEntityType.SELECTION,
                MarketProviderMapping.is_active.is_(True),
                Selection.market_id == market_id,
            )
        )
        return list((await self.session.scalars(statement)).all())

    async def has_active_selection_mapping(self, selection_id: UUID) -> bool:
        """Determine whether any provider still quotes a canonical selection."""
        statement = select(MarketProviderMapping.id).where(
            MarketProviderMapping.entity_type == MarketProviderEntityType.SELECTION,
            MarketProviderMapping.canonical_entity_id == selection_id,
            MarketProviderMapping.is_active.is_(True),
        )
        return (await self.session.scalar(statement)) is not None

    @staticmethod
    def deactivate_mapping(mapping: MarketProviderMapping, observed_at: datetime) -> None:
        """Retire a provider-specific selection listing without deleting historical identity evidence."""
        mapping.is_active = False
        mapping.removed_at = observed_at
        mapping.last_seen_at = observed_at

    async def previous_snapshot(
        self,
        *,
        provider_name: str,
        bookmaker_id: UUID,
        selection_id: UUID,
        observed_at: datetime,
    ) -> OddsSnapshot | None:
        """Return the nearest preceding or same-time snapshot for movement comparison."""
        statement = (
            select(OddsSnapshot)
            .where(
                OddsSnapshot.provider_name == provider_name,
                OddsSnapshot.bookmaker_id == bookmaker_id,
                OddsSnapshot.selection_id == selection_id,
                OddsSnapshot.observed_at <= observed_at,
            )
            .order_by(desc(OddsSnapshot.observed_at), desc(OddsSnapshot.created_at))
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def latest_snapshot(
        self, *, provider_name: str, bookmaker_id: UUID, selection_id: UUID
    ) -> OddsSnapshot | None:
        """Return the most recently observed snapshot for closing and removal movement evidence."""
        statement = (
            select(OddsSnapshot)
            .where(
                OddsSnapshot.provider_name == provider_name,
                OddsSnapshot.bookmaker_id == bookmaker_id,
                OddsSnapshot.selection_id == selection_id,
            )
            .order_by(desc(OddsSnapshot.observed_at), desc(OddsSnapshot.created_at))
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def create_snapshot_once(
        self,
        *,
        ingestion_run_id: UUID,
        raw_payload_id: UUID,
        provider_name: str,
        bookmaker_id: UUID,
        fixture_id: UUID,
        market_id: UUID,
        selection_id: UUID,
        decimal_odds: Decimal,
        implied_probability: Decimal,
        observed_at: datetime,
        checksum: str,
    ) -> tuple[OddsSnapshot | None, bool]:
        """Append one immutable observation once; duplicate exact observations are ignored."""
        statement = select(OddsSnapshot).where(
            OddsSnapshot.provider_name == provider_name,
            OddsSnapshot.bookmaker_id == bookmaker_id,
            OddsSnapshot.selection_id == selection_id,
            OddsSnapshot.observed_at == observed_at,
            OddsSnapshot.checksum == checksum,
        )
        existing = await self.session.scalar(statement)
        if existing is not None:
            return existing, False

        snapshot = OddsSnapshot(
            ingestion_run_id=ingestion_run_id,
            raw_payload_id=raw_payload_id,
            provider_name=provider_name,
            bookmaker_id=bookmaker_id,
            fixture_id=fixture_id,
            market_id=market_id,
            selection_id=selection_id,
            decimal_odds=decimal_odds,
            implied_probability=implied_probability,
            observed_at=observed_at,
            checksum=checksum,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(snapshot)
                await self.session.flush()
        except IntegrityError:
            existing = await self.session.scalar(statement)
            return existing, False
        return snapshot, True

    def add_movement(
        self,
        *,
        ingestion_run_id: UUID,
        raw_payload_id: UUID,
        bookmaker_id: UUID,
        market_id: UUID,
        selection_id: UUID | None,
        previous_snapshot_id: UUID | None,
        current_snapshot_id: UUID | None,
        movement_type: OddsMovementType,
        previous_decimal_odds: Decimal | None,
        current_decimal_odds: Decimal | None,
        observed_at: datetime,
        details: dict[str, Any],
    ) -> OddsMovement:
        """Append one detected movement; no historical price or movement record is overwritten."""
        delta = (
            current_decimal_odds - previous_decimal_odds
            if current_decimal_odds is not None and previous_decimal_odds is not None
            else None
        )
        movement = OddsMovement(
            ingestion_run_id=ingestion_run_id,
            raw_payload_id=raw_payload_id,
            bookmaker_id=bookmaker_id,
            market_id=market_id,
            selection_id=selection_id,
            previous_snapshot_id=previous_snapshot_id,
            current_snapshot_id=current_snapshot_id,
            movement_type=movement_type,
            previous_decimal_odds=previous_decimal_odds,
            current_decimal_odds=current_decimal_odds,
            delta_decimal_odds=delta,
            observed_at=observed_at,
            details=details,
        )
        self.session.add(movement)
        return movement

    def add_audit(
        self,
        *,
        ingestion_run_id: UUID,
        raw_payload_id: UUID,
        fixture_id: UUID | None,
        provider_name: str,
        provider_fixture_id: str | None,
        outcome: OddsAuditOutcome,
        checksum: str,
        changes: dict[str, Any],
        snapshots_created: int,
        snapshots_ignored: int,
        movements_detected: int,
    ) -> OddsAudit:
        """Append one auditable summary for raw payload validation and applied changes."""
        audit = OddsAudit(
            ingestion_run_id=ingestion_run_id,
            raw_payload_id=raw_payload_id,
            fixture_id=fixture_id,
            provider_name=provider_name,
            provider_fixture_id=provider_fixture_id,
            outcome=outcome,
            checksum=checksum,
            changes=changes,
            snapshots_created=snapshots_created,
            snapshots_ignored=snapshots_ignored,
            movements_detected=movements_detected,
        )
        self.session.add(audit)
        return audit

    def add_outbox_event(
        self,
        *,
        ingestion_run_id: UUID,
        raw_payload_id: UUID,
        event_type: MarketDataEventType,
        event_key_suffix: str,
        payload: dict[str, Any],
    ) -> MarketDataOutboxEvent:
        """Append a deterministic outbox event as part of the active database transaction."""
        event = MarketDataOutboxEvent(
            ingestion_run_id=ingestion_run_id,
            raw_payload_id=raw_payload_id,
            event_type=event_type,
            event_key=f"{event_type.value}:{raw_payload_id}:{event_key_suffix}",
            payload=payload,
        )
        self.session.add(event)
        return event

    @staticmethod
    def complete_run(run: OddsIngestionRun, *, has_failures: bool) -> None:
        """Set terminal run state only after the caller has processed all raw payloads."""
        run.status = (
            OddsIngestionRunStatus.COMPLETED_WITH_ERRORS
            if has_failures
            else OddsIngestionRunStatus.COMPLETED
        )
        run.completed_at = datetime.now(UTC)
