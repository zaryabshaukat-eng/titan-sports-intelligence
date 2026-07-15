"""Transactional orchestration for the provider-neutral fixture ingestion pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.ingestion.enums import (
    IngestionAuditOutcome,
    IngestionEventType,
    RawPayloadStatus,
)
from app.modules.ingestion.exceptions import ImmutableFixtureConflictError, PayloadValidationError
from app.modules.ingestion.models import (
    FixtureIngestionRun,
    RawFixturePayload,
)
from app.modules.ingestion.providers.base import FixtureProviderAdapter
from app.modules.ingestion.repositories import IngestionRepository
from app.modules.ingestion.resolver import CanonicalEntityResolver, ResolvedFixtureReferences
from app.modules.ingestion.schemas import (
    FixtureIngestionBatchResult,
    FixtureIngestionItemResult,
    NormalizedFixture,
)
from app.modules.sports.models import Fixture, FixtureOfficial, FixtureStatusHistory

logger = get_logger(__name__)


def payload_checksum(payload: dict[str, Any]) -> str:
    """Hash canonicalized JSON so semantically identical object key order retries deduplicate."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def idempotency_key(provider_name: str, checksum: str) -> str:
    """Namespace payload checksum by provider to prevent accidental cross-provider deduplication."""
    return hashlib.sha256(f"{provider_name}\x00{checksum}".encode()).hexdigest()


class FixtureIngestionService:
    """Process one provider batch atomically while retaining every accepted raw payload."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        provider_adapter: FixtureProviderAdapter,
    ) -> None:
        self.session = session
        self.provider_adapter = provider_adapter
        self.repository = IngestionRepository(session)
        self.resolver = CanonicalEntityResolver(
            session=session,
            ingestion_repository=self.repository,
            provider_name=provider_adapter.provider_name,
        )

    async def ingest(self, payloads: list[dict[str, Any]]) -> FixtureIngestionBatchResult:
        """Validate, resolve, upsert, audit, and enqueue events for a provider payload batch."""
        run = await self.repository.create_run(self.provider_adapter.provider_name, len(payloads))
        item_results: list[FixtureIngestionItemResult] = []

        for source_index, payload in enumerate(payloads):
            result = await self._ingest_one(run, source_index, payload)
            item_results.append(result)

        self.repository.complete_run(run, has_failures=run.failed_count > 0)
        if run.failed_count:
            run.failure_summary = f"{run.failed_count} payload(s) failed validation."
        await self.session.flush()

        logger.info(
            "ingestion.fixture_batch_completed",
            extra={
                "extra_fields": {
                    "run_id": str(run.id),
                    "provider": run.provider_name,
                    "received": run.received_count,
                    "inserted": run.inserted_count,
                    "updated": run.updated_count,
                    "unchanged": run.unchanged_count,
                    "failed": run.failed_count,
                }
            },
        )
        return FixtureIngestionBatchResult(
            run_id=run.id,
            provider_name=run.provider_name,
            received_count=run.received_count,
            inserted_count=run.inserted_count,
            updated_count=run.updated_count,
            unchanged_count=run.unchanged_count,
            failed_count=run.failed_count,
            items=item_results,
        )

    async def _ingest_one(
        self,
        run: FixtureIngestionRun,
        source_index: int,
        payload: dict[str, Any],
    ) -> FixtureIngestionItemResult:
        """Process one raw payload without allowing validation failure to abort its batch."""
        checksum = payload_checksum(payload)
        raw_payload, is_new = await self.repository.create_raw_payload_once(
            run=run,
            provider_name=self.provider_adapter.provider_name,
            provider_fixture_id=self.provider_adapter.extract_fixture_id(payload),
            checksum=checksum,
            idempotency_key=idempotency_key(self.provider_adapter.provider_name, checksum),
            payload=payload,
        )
        if not is_new:
            run.unchanged_count += 1
            self.repository.add_audit_entry(
                run_id=run.id,
                raw_payload_id=raw_payload.id,
                fixture_id=raw_payload.canonical_fixture_id,
                provider_name=run.provider_name,
                provider_fixture_id=raw_payload.provider_fixture_id,
                outcome=IngestionAuditOutcome.UNCHANGED,
                checksum=checksum,
                changes={"reason": "idempotent_replay", "source_index": source_index},
            )
            return FixtureIngestionItemResult(
                source_index=source_index,
                outcome=IngestionAuditOutcome.UNCHANGED,
                fixture_id=raw_payload.canonical_fixture_id,
            )

        try:
            normalized = self.provider_adapter.normalize(payload)
            raw_payload.provider_fixture_id = normalized.provider_fixture_id
            raw_payload.validation_status = RawPayloadStatus.VALID
            # Roll back any partially resolved master data or attempted fixture
            # mutation while retaining the already-received immutable raw payload.
            async with self.session.begin_nested():
                references = await self.resolver.resolve(normalized)
                fixture, outcome, changes = await self._upsert_fixture(
                    raw_payload=raw_payload,
                    normalized=normalized,
                    references=references,
                )
        except PayloadValidationError as exc:
            return self._record_validation_failure(
                run=run,
                source_index=source_index,
                raw_payload=raw_payload,
                checksum=checksum,
                errors=exc.errors,
            )

        raw_payload.canonical_fixture_id = fixture.id
        raw_payload.validation_status = RawPayloadStatus.APPLIED
        raw_payload.processed_at = datetime.now(UTC)
        self.repository.add_audit_entry(
            run_id=run.id,
            raw_payload_id=raw_payload.id,
            fixture_id=fixture.id,
            provider_name=run.provider_name,
            provider_fixture_id=normalized.provider_fixture_id,
            outcome=outcome,
            checksum=checksum,
            changes=changes,
        )
        if outcome is IngestionAuditOutcome.INSERTED:
            run.inserted_count += 1
            self.repository.add_outbox_event(
                run_id=run.id,
                raw_payload_id=raw_payload.id,
                fixture_id=fixture.id,
                event_type=IngestionEventType.FIXTURE_INGESTED,
                payload=self._event_payload(run, raw_payload, fixture.id, changes),
            )
        elif outcome is IngestionAuditOutcome.UPDATED:
            run.updated_count += 1
            self.repository.add_outbox_event(
                run_id=run.id,
                raw_payload_id=raw_payload.id,
                fixture_id=fixture.id,
                event_type=IngestionEventType.FIXTURE_UPDATED,
                payload=self._event_payload(run, raw_payload, fixture.id, changes),
            )
        else:
            run.unchanged_count += 1

        return FixtureIngestionItemResult(
            source_index=source_index,
            outcome=outcome,
            fixture_id=fixture.id,
        )

    def _record_validation_failure(
        self,
        *,
        run: FixtureIngestionRun,
        source_index: int,
        raw_payload: RawFixturePayload,
        checksum: str,
        errors: list[dict[str, Any]],
    ) -> FixtureIngestionItemResult:
        """Persist an invalid raw payload and its event without exposing raw JSON in responses."""
        raw_payload.validation_status = RawPayloadStatus.INVALID
        raw_payload.validation_errors = errors
        raw_payload.processed_at = datetime.now(UTC)
        run.failed_count += 1
        changes: dict[str, Any] = {"source_index": source_index, "validation_errors": errors}
        self.repository.add_audit_entry(
            run_id=run.id,
            raw_payload_id=raw_payload.id,
            fixture_id=None,
            provider_name=run.provider_name,
            provider_fixture_id=raw_payload.provider_fixture_id,
            outcome=IngestionAuditOutcome.VALIDATION_FAILED,
            checksum=checksum,
            changes=changes,
        )
        self.repository.add_outbox_event(
            run_id=run.id,
            raw_payload_id=raw_payload.id,
            fixture_id=None,
            event_type=IngestionEventType.FIXTURE_VALIDATION_FAILED,
            payload={
                "run_id": str(run.id),
                "provider": run.provider_name,
                "provider_fixture_id": raw_payload.provider_fixture_id,
                "raw_payload_id": str(raw_payload.id),
                "validation_errors": errors,
            },
        )
        logger.warning(
            "ingestion.fixture_validation_failed",
            extra={
                "extra_fields": {
                    "run_id": str(run.id),
                    "provider": run.provider_name,
                    "raw_payload_id": str(raw_payload.id),
                    "error_count": len(errors),
                }
            },
        )
        return FixtureIngestionItemResult(
            source_index=source_index,
            outcome=IngestionAuditOutcome.VALIDATION_FAILED,
            validation_errors=errors,
        )

    async def _upsert_fixture(
        self,
        *,
        raw_payload: RawFixturePayload,
        normalized: NormalizedFixture,
        references: ResolvedFixtureReferences,
    ) -> tuple[Fixture, IngestionAuditOutcome, dict[str, Any]]:
        """Create a fixture or update only its declared mutable scheduling fields."""
        identity = await self.repository.get_fixture_identity(
            self.provider_adapter.provider_name, normalized.provider_fixture_id
        )
        fixture_created = False
        identity_created = False
        if identity is not None:
            fixture = await self.session.get(Fixture, identity.fixture_id)
            if fixture is None:
                raise PayloadValidationError(
                    [
                        {
                            "path": "fixture_identity",
                            "message": (
                                "provider fixture identity points to a missing canonical fixture"
                            ),
                            "type": "broken_fixture_identity",
                        }
                    ]
                )
            self._validate_immutable_fixture_identity(fixture, references)
        else:
            fixture = await self.repository.get_fixture_by_natural_key(
                season_id=references.season_id,
                home_team_id=references.home_team_id,
                away_team_id=references.away_team_id,
                scheduled_start_at=normalized.scheduled_start_at,
            )
            if fixture is None:
                fixture = Fixture(
                    season_id=references.season_id,
                    home_team_id=references.home_team_id,
                    away_team_id=references.away_team_id,
                    fixture_status_id=references.fixture_status_id,
                    venue_id=references.venue_id,
                    timezone_id=references.timezone_id,
                    scheduled_start_at=normalized.scheduled_start_at,
                    scheduled_end_at=normalized.scheduled_end_at,
                    round_name=normalized.round_name,
                    stage_name=normalized.stage_name,
                )
                self.session.add(fixture)
                await self.session.flush()
                self.session.add(
                    FixtureStatusHistory(
                        fixture_id=fixture.id,
                        fixture_status_id=references.fixture_status_id,
                        effective_at=datetime.now(UTC),
                    )
                )
                fixture_created = True
            identity = await self.repository.create_fixture_identity(
                provider_name=self.provider_adapter.provider_name,
                provider_fixture_id=normalized.provider_fixture_id,
                fixture_id=fixture.id,
                raw_payload_id=raw_payload.id,
                checksum=raw_payload.checksum,
            )
            identity_created = True

        changes = (
            {}
            if fixture_created
            else self._apply_mutable_fixture_changes(fixture, normalized, references)
        )
        if not fixture_created and changes.get("fixture_status_id") is not None:
            self.session.add(
                FixtureStatusHistory(
                    fixture_id=fixture.id,
                    fixture_status_id=references.fixture_status_id,
                    effective_at=datetime.now(UTC),
                )
            )

        official_changes = await self._synchronize_officials(fixture, normalized)
        if official_changes:
            changes["official_assignments"] = official_changes
        if identity_created:
            changes["provider_identity_linked"] = True
        identity.latest_raw_payload_id = raw_payload.id
        identity.last_checksum = raw_payload.checksum
        identity.last_seen_at = datetime.now(UTC)

        if fixture_created:
            return (
                fixture,
                IngestionAuditOutcome.INSERTED,
                {
                    "created": True,
                    "provider_identity_linked": True,
                    "official_assignments": official_changes,
                },
            )
        if changes:
            return fixture, IngestionAuditOutcome.UPDATED, changes
        return fixture, IngestionAuditOutcome.UNCHANGED, {}

    @staticmethod
    def _validate_immutable_fixture_identity(
        fixture: Fixture, references: ResolvedFixtureReferences
    ) -> None:
        """Reject identity-changing provider updates rather than silently rewriting history."""
        comparisons = {
            "season_id": (fixture.season_id, references.season_id),
            "home_team_id": (fixture.home_team_id, references.home_team_id),
            "away_team_id": (fixture.away_team_id, references.away_team_id),
        }
        conflicts = [
            {
                "path": field_name,
                "message": (
                    "provider payload attempts to change an immutable fixture identity field"
                ),
                "type": "immutable_fixture_conflict",
            }
            for field_name, (current, incoming) in comparisons.items()
            if current != incoming
        ]
        if conflicts:
            raise ImmutableFixtureConflictError(conflicts)

    @staticmethod
    def _apply_mutable_fixture_changes(
        fixture: Fixture,
        normalized: NormalizedFixture,
        references: ResolvedFixtureReferences,
    ) -> dict[str, dict[str, str | None]]:
        """Apply a small, explicit whitelist of mutable fixture scheduling attributes."""
        desired_values: dict[str, Any] = {
            "fixture_status_id": references.fixture_status_id,
            "venue_id": references.venue_id,
            "timezone_id": references.timezone_id,
            "scheduled_start_at": normalized.scheduled_start_at,
            "scheduled_end_at": normalized.scheduled_end_at,
            "round_name": normalized.round_name,
            "stage_name": normalized.stage_name,
        }
        changes: dict[str, dict[str, str | None]] = {}
        for field_name, incoming_value in desired_values.items():
            current_value = getattr(fixture, field_name)
            if current_value == incoming_value:
                continue
            changes[field_name] = {
                "from": FixtureIngestionService._audit_value(current_value),
                "to": FixtureIngestionService._audit_value(incoming_value),
            }
            setattr(fixture, field_name, incoming_value)
        return changes

    async def _synchronize_officials(
        self, fixture: Fixture, normalized: NormalizedFixture
    ) -> list[dict[str, str | int]]:
        """Update supplied official assignments without removing omitted partial-feed data."""
        if not normalized.officials:
            return []
        existing_assignments = list(
            (
                await self.session.scalars(
                    select(FixtureOfficial).where(FixtureOfficial.fixture_id == fixture.id)
                )
            ).all()
        )
        by_official_id = {assignment.official_id: assignment for assignment in existing_assignments}
        by_slot = {
            (assignment.role, assignment.assignment_order): assignment
            for assignment in existing_assignments
        }
        changes: list[dict[str, str | int]] = []
        for normalized_official in normalized.officials:
            official = await self.resolver.resolve_official(normalized_official)
            desired_slot = (normalized_official.role, normalized_official.assignment_order)
            existing = by_official_id.get(official.id)
            occupant = by_slot.get(desired_slot)
            if occupant is not None and occupant.official_id != official.id:
                raise PayloadValidationError(
                    [
                        {
                            "path": "officials",
                            "message": (
                                "official assignment role and order conflicts with "
                                "existing fixture data"
                            ),
                            "type": "official_assignment_conflict",
                        }
                    ]
                )
            if existing is None:
                assignment = FixtureOfficial(
                    fixture_id=fixture.id,
                    official_id=official.id,
                    role=normalized_official.role,
                    assignment_order=normalized_official.assignment_order,
                )
                self.session.add(assignment)
                by_official_id[official.id] = assignment
                by_slot[desired_slot] = assignment
                changes.append(
                    {
                        "action": "added",
                        "official_id": str(official.id),
                        "role": normalized_official.role.value,
                        "assignment_order": normalized_official.assignment_order,
                    }
                )
                continue
            if (existing.role, existing.assignment_order) == desired_slot:
                continue
            previous_slot = (existing.role, existing.assignment_order)
            by_slot.pop(previous_slot, None)
            existing.role = normalized_official.role
            existing.assignment_order = normalized_official.assignment_order
            by_slot[desired_slot] = existing
            changes.append(
                {
                    "action": "updated",
                    "official_id": str(official.id),
                    "role": normalized_official.role.value,
                    "assignment_order": normalized_official.assignment_order,
                }
            )
        return changes

    @staticmethod
    def _audit_value(value: Any) -> str | None:
        """Serialize scalar audit values safely for JSONB change records."""
        return str(value) if value is not None else None

    @staticmethod
    def _event_payload(
        run: FixtureIngestionRun,
        raw_payload: RawFixturePayload,
        fixture_id: UUID,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        """Create event metadata without duplicating the original provider payload."""
        return {
            "run_id": str(run.id),
            "provider": run.provider_name,
            "provider_fixture_id": raw_payload.provider_fixture_id,
            "raw_payload_id": str(raw_payload.id),
            "fixture_id": str(fixture_id),
            "checksum": raw_payload.checksum,
            "changes": changes,
        }
