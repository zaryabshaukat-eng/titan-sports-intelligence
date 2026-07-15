"""Async repositories for ingestion provenance, provider identities, and the outbox."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.enums import (
    IngestionAuditOutcome,
    IngestionEventType,
    IngestionRunStatus,
    ProviderEntityType,
    RawPayloadStatus,
)
from app.modules.ingestion.models import (
    FixtureIngestionAudit,
    FixtureIngestionRun,
    FixtureProviderIdentity,
    IngestionOutboxEvent,
    ProviderEntityIdentity,
    RawFixturePayload,
)
from app.modules.sports.models import Fixture


class IngestionRepository:
    """Persist ingestion operational records without provider-specific business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, provider_name: str, received_count: int) -> FixtureIngestionRun:
        """Start and flush one auditable provider batch run."""
        run = FixtureIngestionRun(
            provider_name=provider_name,
            status=IngestionRunStatus.RUNNING,
            received_count=received_count,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_raw_payload_by_idempotency_key(
        self, provider_name: str, idempotency_key: str
    ) -> RawFixturePayload | None:
        """Find the first immutable receipt for a provider-specific payload key."""
        statement = select(RawFixturePayload).where(
            RawFixturePayload.provider_name == provider_name,
            RawFixturePayload.idempotency_key == idempotency_key,
        )
        return await self.session.scalar(statement)

    async def create_raw_payload_once(
        self,
        *,
        run: FixtureIngestionRun,
        provider_name: str,
        provider_fixture_id: str | None,
        checksum: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> tuple[RawFixturePayload, bool]:
        """Persist a raw payload exactly once, including when concurrent retries race.

        A nested transaction rolls back only the duplicate insert attempt; the
        surrounding ingestion run can still append its idempotent-replay audit entry.
        """
        existing = await self.get_raw_payload_by_idempotency_key(provider_name, idempotency_key)
        if existing is not None:
            return existing, False

        raw_payload = RawFixturePayload(
            ingestion_run_id=run.id,
            provider_name=provider_name,
            provider_fixture_id=provider_fixture_id,
            checksum=checksum,
            idempotency_key=idempotency_key,
            payload=payload,
            validation_status=RawPayloadStatus.RECEIVED,
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

    async def get_fixture_identity(
        self, provider_name: str, provider_fixture_id: str
    ) -> FixtureProviderIdentity | None:
        """Load and lock a provider fixture identity before a mutable fixture upsert."""
        statement = (
            select(FixtureProviderIdentity)
            .where(
                FixtureProviderIdentity.provider_name == provider_name,
                FixtureProviderIdentity.provider_fixture_id == provider_fixture_id,
            )
            .with_for_update()
        )
        return await self.session.scalar(statement)

    async def get_fixture_by_natural_key(
        self,
        *,
        season_id: UUID,
        home_team_id: UUID,
        away_team_id: UUID,
        scheduled_start_at: datetime,
    ) -> Fixture | None:
        """Find an existing canonical fixture before linking a new provider identity."""
        statement = select(Fixture).where(
            Fixture.season_id == season_id,
            Fixture.home_team_id == home_team_id,
            Fixture.away_team_id == away_team_id,
            Fixture.scheduled_start_at == scheduled_start_at,
        )
        return await self.session.scalar(statement)

    async def create_fixture_identity(
        self,
        *,
        provider_name: str,
        provider_fixture_id: str,
        fixture_id: UUID,
        raw_payload_id: UUID,
        checksum: str,
    ) -> FixtureProviderIdentity:
        """Link one external fixture identity to one canonical fixture."""
        identity = FixtureProviderIdentity(
            provider_name=provider_name,
            provider_fixture_id=provider_fixture_id,
            fixture_id=fixture_id,
            latest_raw_payload_id=raw_payload_id,
            last_checksum=checksum,
        )
        self.session.add(identity)
        await self.session.flush()
        return identity

    async def get_provider_entity_identity(
        self,
        provider_name: str,
        entity_type: ProviderEntityType,
        provider_entity_id: str,
    ) -> ProviderEntityIdentity | None:
        """Find a provider-neutral external-to-canonical master-data identity link."""
        statement = select(ProviderEntityIdentity).where(
            ProviderEntityIdentity.provider_name == provider_name,
            ProviderEntityIdentity.entity_type == entity_type,
            ProviderEntityIdentity.provider_entity_id == provider_entity_id,
        )
        return await self.session.scalar(statement)

    async def link_provider_entity(
        self,
        *,
        provider_name: str,
        entity_type: ProviderEntityType,
        provider_entity_id: str,
        canonical_entity_id: UUID,
    ) -> ProviderEntityIdentity:
        """Persist a stable provider-to-canonical identity mapping once."""
        existing = await self.get_provider_entity_identity(
            provider_name, entity_type, provider_entity_id
        )
        if existing is not None:
            return existing

        identity = ProviderEntityIdentity(
            provider_name=provider_name,
            entity_type=entity_type,
            provider_entity_id=provider_entity_id,
            canonical_entity_id=canonical_entity_id,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(identity)
                await self.session.flush()
        except IntegrityError:
            existing = await self.get_provider_entity_identity(
                provider_name, entity_type, provider_entity_id
            )
            if existing is None:
                raise
            return existing
        return identity

    def add_audit_entry(
        self,
        *,
        run_id: UUID,
        raw_payload_id: UUID,
        fixture_id: UUID | None,
        provider_name: str,
        provider_fixture_id: str | None,
        outcome: IngestionAuditOutcome,
        checksum: str,
        changes: dict[str, Any],
    ) -> FixtureIngestionAudit:
        """Append a business-visible audit record for every input outcome."""
        audit_entry = FixtureIngestionAudit(
            ingestion_run_id=run_id,
            raw_payload_id=raw_payload_id,
            fixture_id=fixture_id,
            provider_name=provider_name,
            provider_fixture_id=provider_fixture_id,
            outcome=outcome,
            checksum=checksum,
            changes=changes,
        )
        self.session.add(audit_entry)
        return audit_entry

    def add_outbox_event(
        self,
        *,
        run_id: UUID,
        raw_payload_id: UUID,
        fixture_id: UUID | None,
        event_type: IngestionEventType,
        payload: dict[str, Any],
    ) -> IngestionOutboxEvent:
        """Append a deduplicated transactional-outbox event in the active SQL transaction."""
        event = IngestionOutboxEvent(
            ingestion_run_id=run_id,
            raw_payload_id=raw_payload_id,
            fixture_id=fixture_id,
            event_type=event_type,
            event_key=f"{event_type.value}:{raw_payload_id}",
            payload=payload,
        )
        self.session.add(event)
        return event

    @staticmethod
    def complete_run(run: FixtureIngestionRun, *, has_failures: bool) -> None:
        """Record terminal counters only after every accepted input has been handled."""
        run.status = (
            IngestionRunStatus.COMPLETED_WITH_ERRORS
            if has_failures
            else IngestionRunStatus.COMPLETED
        )
        run.completed_at = datetime.now(UTC)
