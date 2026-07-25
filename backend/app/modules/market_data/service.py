"""Transactional service for immutable market-data and odds ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.market_data.enums import (
    MarketDataEventType,
    OddsAuditOutcome,
    OddsMovementType,
    RawOddsPayloadStatus,
)
from app.modules.market_data.exceptions import OddsPayloadValidationError
from app.modules.market_data.models import (
    Market,
    MarketStatus,
    OddsIngestionRun,
    OddsSnapshot,
    RawOddsPayload,
    Selection,
)
from app.modules.market_data.providers.base import OddsProviderAdapter
from app.modules.market_data.repositories import MarketDataIngestionRepository
from app.modules.market_data.resolver import MarketDataEntityResolver, ResolvedMarket
from app.modules.market_data.schemas import (
    NormalizedMarket,
    NormalizedOddsPayload,
    OddsIngestionBatchResult,
    OddsIngestionItemResult,
)

logger = get_logger(__name__)


def payload_checksum(payload: dict[str, Any]) -> str:
    """Create a deterministic source-payload checksum independent of JSON object key ordering."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def idempotency_key(provider_name: str, checksum: str) -> str:
    """Scope a content hash to one source provider for retry-safe receipt deduplication."""
    return hashlib.sha256(f"{provider_name}\x00{checksum}".encode()).hexdigest()


@dataclass(slots=True)
class _ApplyStats:
    """Mutable per-payload accounting used to write audit and API summaries."""

    snapshots_created: int = 0
    snapshots_ignored: int = 0
    movements_detected: int = 0
    event_sequence: int = 0
    changes: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {
            "price_movements": [],
            "market_status_changes": [],
            "selection_additions": [],
            "selection_removals": [],
            "out_of_order_statuses": [],
        }
    )


class OddsIngestionService:
    """Normalize, resolve, append immutable odds, and record every outcome in one transaction."""

    def __init__(self, *, session: AsyncSession, provider_adapter: OddsProviderAdapter) -> None:
        self.session = session
        self.provider_adapter = provider_adapter
        self.repository = MarketDataIngestionRepository(session)
        self.resolver = MarketDataEntityResolver(
            session=session,
            repository=self.repository,
            provider_name=provider_adapter.provider_name,
        )

    async def ingest(self, payloads: list[dict[str, Any]]) -> OddsIngestionBatchResult:
        """Ingest one provider batch while retaining raw evidence for every accepted input."""
        run = await self.repository.create_run(self.provider_adapter.provider_name, len(payloads))
        item_results: list[OddsIngestionItemResult] = []

        for source_index, payload in enumerate(payloads):
            item_results.append(await self._ingest_one(run, source_index, payload))

        self.repository.complete_run(run, has_failures=run.failed_count > 0)
        if run.failed_count:
            run.failure_summary = f"{run.failed_count} payload(s) failed validation."
        await self.session.flush()
        logger.info(
            "market_data.odds_batch_completed",
            extra={
                "extra_fields": {
                    "run_id": str(run.id),
                    "provider": run.provider_name,
                    "received": run.received_count,
                    "snapshots_created": run.snapshots_created_count,
                    "snapshots_ignored": run.snapshots_ignored_count,
                    "movements": run.movements_count,
                    "failed": run.failed_count,
                }
            },
        )
        return OddsIngestionBatchResult(
            run_id=run.id,
            provider_name=run.provider_name,
            received_count=run.received_count,
            snapshots_created_count=run.snapshots_created_count,
            snapshots_ignored_count=run.snapshots_ignored_count,
            movements_count=run.movements_count,
            failed_count=run.failed_count,
            items=item_results,
        )

    async def _ingest_one(
        self,
        run: OddsIngestionRun,
        source_index: int,
        payload: dict[str, Any],
    ) -> OddsIngestionItemResult:
        """Receive one payload once while isolating validation failures from its batch."""
        checksum = payload_checksum(payload)
        fixture_provider_name, provider_fixture_id = (
            self.provider_adapter.extract_fixture_reference(payload)
        )
        raw_payload, is_new = await self.repository.create_raw_payload_once(
            run=run,
            provider_name=self.provider_adapter.provider_name,
            fixture_provider_name=fixture_provider_name,
            provider_fixture_id=provider_fixture_id,
            checksum=checksum,
            idempotency_key=idempotency_key(self.provider_adapter.provider_name, checksum),
            payload=payload,
        )
        if not is_new:
            run.snapshots_ignored_count += 1
            self.repository.add_audit(
                ingestion_run_id=run.id,
                raw_payload_id=raw_payload.id,
                fixture_id=raw_payload.canonical_fixture_id,
                provider_name=run.provider_name,
                provider_fixture_id=raw_payload.provider_fixture_id,
                outcome=OddsAuditOutcome.UNCHANGED,
                checksum=checksum,
                changes={"reason": "idempotent_replay", "source_index": source_index},
                snapshots_created=0,
                snapshots_ignored=1,
                movements_detected=0,
            )
            return OddsIngestionItemResult(
                source_index=source_index,
                outcome=OddsAuditOutcome.UNCHANGED,
                fixture_id=raw_payload.canonical_fixture_id,
                snapshots_created=0,
                snapshots_ignored=1,
                movements_detected=0,
            )

        try:
            normalized = self.provider_adapter.normalize(payload)
            raw_payload.fixture_provider_name = normalized.fixture_provider_name
            raw_payload.provider_fixture_id = normalized.provider_fixture_id
            raw_payload.validation_status = RawOddsPayloadStatus.VALID
            # Preserve the raw receipt even if semantic resolution detects an
            # unresolved fixture or identity conflict after DTO validation.
            async with self.session.begin_nested():
                fixture = await self.resolver.resolve_fixture(normalized)
                stats = await self._apply_payload(run, raw_payload, fixture.id, normalized)
        except OddsPayloadValidationError as exc:
            return self._record_validation_failure(
                run=run,
                source_index=source_index,
                raw_payload=raw_payload,
                checksum=checksum,
                errors=exc.errors,
            )

        raw_payload.canonical_fixture_id = fixture.id
        raw_payload.validation_status = RawOddsPayloadStatus.APPLIED
        raw_payload.processed_at = datetime.now(UTC)
        outcome = (
            OddsAuditOutcome.PROCESSED
            if stats.snapshots_created or stats.movements_detected
            else OddsAuditOutcome.UNCHANGED
        )
        self.repository.add_audit(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            fixture_id=fixture.id,
            provider_name=run.provider_name,
            provider_fixture_id=normalized.provider_fixture_id,
            outcome=outcome,
            checksum=checksum,
            changes=stats.changes,
            snapshots_created=stats.snapshots_created,
            snapshots_ignored=stats.snapshots_ignored,
            movements_detected=stats.movements_detected,
        )
        run.snapshots_created_count += stats.snapshots_created
        run.snapshots_ignored_count += stats.snapshots_ignored
        run.movements_count += stats.movements_detected
        return OddsIngestionItemResult(
            source_index=source_index,
            outcome=outcome,
            fixture_id=fixture.id,
            snapshots_created=stats.snapshots_created,
            snapshots_ignored=stats.snapshots_ignored,
            movements_detected=stats.movements_detected,
        )

    async def _apply_payload(
        self,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        normalized: NormalizedOddsPayload,
    ) -> _ApplyStats:
        """Apply one validated payload as immutable snapshots and append-only movement records."""
        stats = _ApplyStats()
        bookmaker = await self.resolver.resolve_bookmaker(normalized.bookmaker)
        for normalized_market in normalized.markets:
            resolved_market = await self.resolver.resolve_market(
                fixture_id=fixture_id,
                value=normalized_market,
                observed_at=normalized.observed_at,
            )
            await self._apply_market(
                run=run,
                raw_payload=raw_payload,
                fixture_id=fixture_id,
                bookmaker_id=bookmaker.id,
                normalized_market=normalized_market,
                resolved_market=resolved_market,
                observed_at=normalized.observed_at,
                stats=stats,
            )
        return stats

    async def _apply_market(
        self,
        *,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        bookmaker_id: UUID,
        normalized_market: NormalizedMarket,
        resolved_market: ResolvedMarket,
        observed_at: datetime,
        stats: _ApplyStats,
    ) -> None:
        """Persist selection prices and market lifecycle changes for one normalized market."""
        market = resolved_market.market
        active_mappings = {
            mapping.provider_entity_id: mapping
            for mapping in await self.repository.active_selection_mappings_for_market(
                self.provider_adapter.provider_name, market.id
            )
        }
        current_provider_selection_ids: set[str] = set()
        active_selection_ids: list[UUID] = []

        for normalized_selection in normalized_market.selections:
            current_provider_selection_ids.add(normalized_selection.provider_id)
            resolved_selection = await self.resolver.resolve_selection(
                market.id, normalized_selection
            )
            selection = resolved_selection.selection
            active_selection_ids.append(selection.id)
            previous_snapshot = await self.repository.previous_snapshot(
                provider_name=self.provider_adapter.provider_name,
                bookmaker_id=bookmaker_id,
                selection_id=selection.id,
                observed_at=observed_at,
            )
            if (
                previous_snapshot is not None
                and previous_snapshot.decimal_odds == normalized_selection.decimal_odds
            ):
                stats.snapshots_ignored += 1
            else:
                snapshot, created = await self.repository.create_snapshot_once(
                    ingestion_run_id=run.id,
                    raw_payload_id=raw_payload.id,
                    provider_name=self.provider_adapter.provider_name,
                    bookmaker_id=bookmaker_id,
                    fixture_id=fixture_id,
                    market_id=market.id,
                    selection_id=selection.id,
                    decimal_odds=normalized_selection.decimal_odds,
                    implied_probability=normalized_selection.implied_probability,
                    observed_at=observed_at,
                    checksum=raw_payload.checksum,
                )
                if not created or snapshot is None:
                    stats.snapshots_ignored += 1
                else:
                    stats.snapshots_created += 1
                    self._emit_snapshot_event(run, raw_payload, fixture_id, market.id, snapshot)
                    if previous_snapshot is None:
                        self._record_movement(
                            run=run,
                            raw_payload=raw_payload,
                            fixture_id=fixture_id,
                            bookmaker_id=bookmaker_id,
                            market_id=market.id,
                            selection_id=selection.id,
                            previous_snapshot=None,
                            current_snapshot=snapshot,
                            movement_type=OddsMovementType.OPENING,
                            observed_at=observed_at,
                            stats=stats,
                        )
                    else:
                        movement_type = (
                            OddsMovementType.PRICE_INCREASED
                            if snapshot.decimal_odds > previous_snapshot.decimal_odds
                            else OddsMovementType.PRICE_DECREASED
                        )
                        self._record_movement(
                            run=run,
                            raw_payload=raw_payload,
                            fixture_id=fixture_id,
                            bookmaker_id=bookmaker_id,
                            market_id=market.id,
                            selection_id=selection.id,
                            previous_snapshot=previous_snapshot,
                            current_snapshot=snapshot,
                            movement_type=movement_type,
                            observed_at=observed_at,
                            stats=stats,
                        )
            if resolved_selection.was_added_or_reactivated:
                latest_snapshot = await self.repository.latest_snapshot(
                    provider_name=self.provider_adapter.provider_name,
                    bookmaker_id=bookmaker_id,
                    selection_id=selection.id,
                )
                self._record_movement(
                    run=run,
                    raw_payload=raw_payload,
                    fixture_id=fixture_id,
                    bookmaker_id=bookmaker_id,
                    market_id=market.id,
                    selection_id=selection.id,
                    previous_snapshot=None,
                    current_snapshot=latest_snapshot,
                    movement_type=OddsMovementType.SELECTION_ADDED,
                    observed_at=observed_at,
                    stats=stats,
                )
                stats.changes["selection_additions"].append(
                    {"market_id": str(market.id), "selection_id": str(selection.id)}
                )

        if normalized_market.selections_complete:
            await self._detect_selection_removals(
                run=run,
                raw_payload=raw_payload,
                fixture_id=fixture_id,
                bookmaker_id=bookmaker_id,
                market=market,
                prior_active_mappings=active_mappings,
                current_provider_selection_ids=current_provider_selection_ids,
                observed_at=observed_at,
                stats=stats,
            )

        await self._record_market_status_change(
            run=run,
            raw_payload=raw_payload,
            fixture_id=fixture_id,
            bookmaker_id=bookmaker_id,
            market=market,
            resolved_market=resolved_market,
            observed_at=observed_at,
            active_selection_ids=active_selection_ids,
            stats=stats,
        )

    async def _detect_selection_removals(
        self,
        *,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        bookmaker_id: UUID,
        market: Market,
        prior_active_mappings: dict[str, Any],
        current_provider_selection_ids: set[str],
        observed_at: datetime,
        stats: _ApplyStats,
    ) -> None:
        """Record selection removals without deleting canonical selections or snapshots."""
        for provider_selection_id, mapping in prior_active_mappings.items():
            if provider_selection_id in current_provider_selection_ids:
                continue
            selection = await self.session.get(Selection, mapping.canonical_entity_id)
            if selection is None:
                continue
            self.repository.deactivate_mapping(mapping, observed_at)
            if not await self.repository.has_active_selection_mapping(selection.id):
                selection.is_active = False
                selection.removed_at = observed_at
            latest_snapshot = await self.repository.latest_snapshot(
                provider_name=self.provider_adapter.provider_name,
                bookmaker_id=bookmaker_id,
                selection_id=selection.id,
            )
            self._record_movement(
                run=run,
                raw_payload=raw_payload,
                fixture_id=fixture_id,
                bookmaker_id=bookmaker_id,
                market_id=market.id,
                selection_id=selection.id,
                previous_snapshot=latest_snapshot,
                current_snapshot=None,
                movement_type=OddsMovementType.SELECTION_REMOVED,
                observed_at=observed_at,
                stats=stats,
            )
            stats.changes["selection_removals"].append(
                {"market_id": str(market.id), "selection_id": str(selection.id)}
            )

    async def _record_market_status_change(
        self,
        *,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        bookmaker_id: UUID,
        market: Market,
        resolved_market: ResolvedMarket,
        observed_at: datetime,
        active_selection_ids: list[UUID],
        stats: _ApplyStats,
    ) -> None:
        """Emit market status movements only when status data is newer."""
        previous_status = resolved_market.previous_status
        if previous_status is None:
            return
        if not resolved_market.status_applied:
            stats.changes["out_of_order_statuses"].append(
                {"market_id": str(market.id), "status": previous_status.code}
            )
            return
        current_status = await self.session.get(MarketStatus, market.market_status_id)
        if current_status is None or current_status.code == previous_status.code:
            return
        current_status_code = current_status.code
        stats.changes["market_status_changes"].append(
            {
                "market_id": str(market.id),
                "from": previous_status.code,
                "to": current_status_code,
            }
        )
        if current_status_code == "suspended":
            self._record_movement(
                run=run,
                raw_payload=raw_payload,
                fixture_id=fixture_id,
                bookmaker_id=bookmaker_id,
                market_id=market.id,
                selection_id=None,
                previous_snapshot=None,
                current_snapshot=None,
                movement_type=OddsMovementType.MARKET_SUSPENDED,
                observed_at=observed_at,
                stats=stats,
            )
            self._emit_market_event(
                run,
                raw_payload,
                fixture_id,
                market.id,
                MarketDataEventType.MARKET_SUSPENDED,
                "status-suspended",
                {"previous_status": previous_status.code},
            )
        elif previous_status.code == "suspended" and current_status_code == "open":
            self._record_movement(
                run=run,
                raw_payload=raw_payload,
                fixture_id=fixture_id,
                bookmaker_id=bookmaker_id,
                market_id=market.id,
                selection_id=None,
                previous_snapshot=None,
                current_snapshot=None,
                movement_type=OddsMovementType.MARKET_REOPENED,
                observed_at=observed_at,
                stats=stats,
            )
            self._emit_market_event(
                run,
                raw_payload,
                fixture_id,
                market.id,
                MarketDataEventType.MARKET_REOPENED,
                "status-reopened",
                {"previous_status": previous_status.code},
            )
        elif current_status_code == "closed":
            for selection_id in active_selection_ids:
                latest_snapshot = await self.repository.latest_snapshot(
                    provider_name=self.provider_adapter.provider_name,
                    bookmaker_id=bookmaker_id,
                    selection_id=selection_id,
                )
                if latest_snapshot is None:
                    continue
                self._record_movement(
                    run=run,
                    raw_payload=raw_payload,
                    fixture_id=fixture_id,
                    bookmaker_id=bookmaker_id,
                    market_id=market.id,
                    selection_id=selection_id,
                    previous_snapshot=latest_snapshot,
                    current_snapshot=latest_snapshot,
                    movement_type=OddsMovementType.CLOSING,
                    observed_at=observed_at,
                    stats=stats,
                )

    def _record_movement(
        self,
        *,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        bookmaker_id: UUID,
        market_id: UUID,
        selection_id: UUID | None,
        previous_snapshot: OddsSnapshot | None,
        current_snapshot: OddsSnapshot | None,
        movement_type: OddsMovementType,
        observed_at: datetime,
        stats: _ApplyStats,
    ) -> None:
        """Append a movement and its reliable event without changing any prior observation."""
        movement = self.repository.add_movement(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            bookmaker_id=bookmaker_id,
            market_id=market_id,
            selection_id=selection_id,
            previous_snapshot_id=previous_snapshot.id if previous_snapshot is not None else None,
            current_snapshot_id=current_snapshot.id if current_snapshot is not None else None,
            movement_type=movement_type,
            previous_decimal_odds=(
                previous_snapshot.decimal_odds if previous_snapshot is not None else None
            ),
            current_decimal_odds=current_snapshot.decimal_odds
            if current_snapshot is not None
            else None,
            observed_at=observed_at,
            details={"fixture_id": str(fixture_id)},
        )
        stats.movements_detected += 1
        stats.event_sequence += 1
        if movement_type in {OddsMovementType.PRICE_INCREASED, OddsMovementType.PRICE_DECREASED}:
            stats.changes["price_movements"].append(
                {
                    "market_id": str(market_id),
                    "selection_id": str(selection_id) if selection_id is not None else None,
                    "movement": movement_type.value,
                    "from": str(movement.previous_decimal_odds),
                    "to": str(movement.current_decimal_odds),
                }
            )
        if movement_type not in {OddsMovementType.OPENING, OddsMovementType.CLOSING}:
            self.repository.add_outbox_event(
                ingestion_run_id=run.id,
                raw_payload_id=raw_payload.id,
                event_type=MarketDataEventType.ODDS_CHANGED,
                event_key_suffix=f"movement-{stats.event_sequence}",
                payload={
                    "run_id": str(run.id),
                    "provider": run.provider_name,
                    "fixture_id": str(fixture_id),
                    "market_id": str(market_id),
                    "selection_id": str(selection_id) if selection_id is not None else None,
                    "movement_type": movement_type.value,
                    "previous_decimal_odds": str(movement.previous_decimal_odds)
                    if movement.previous_decimal_odds is not None
                    else None,
                    "current_decimal_odds": str(movement.current_decimal_odds)
                    if movement.current_decimal_odds is not None
                    else None,
                },
            )

    def _emit_snapshot_event(
        self,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        market_id: UUID,
        snapshot: OddsSnapshot,
    ) -> None:
        """Enqueue one immutable-snapshot creation event with non-sensitive provenance."""
        self.repository.add_outbox_event(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            event_type=MarketDataEventType.ODDS_SNAPSHOT_CREATED,
            event_key_suffix=f"snapshot-{snapshot.id}",
            payload={
                "run_id": str(run.id),
                "provider": run.provider_name,
                "fixture_id": str(fixture_id),
                "market_id": str(market_id),
                "snapshot_id": str(snapshot.id),
                "selection_id": str(snapshot.selection_id),
                "bookmaker_id": str(snapshot.bookmaker_id),
                "decimal_odds": str(snapshot.decimal_odds),
                "implied_probability": str(snapshot.implied_probability),
                "observed_at": snapshot.observed_at.isoformat(),
            },
        )

    def _emit_market_event(
        self,
        run: OddsIngestionRun,
        raw_payload: RawOddsPayload,
        fixture_id: UUID,
        market_id: UUID,
        event_type: MarketDataEventType,
        event_suffix: str,
        details: dict[str, Any],
    ) -> None:
        """Enqueue a market-lifecycle event alongside its status movement."""
        self.repository.add_outbox_event(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            event_type=event_type,
            event_key_suffix=f"market-{market_id}-{event_suffix}",
            payload={
                "run_id": str(run.id),
                "provider": run.provider_name,
                "fixture_id": str(fixture_id),
                "market_id": str(market_id),
                **details,
            },
        )

    def _record_validation_failure(
        self,
        *,
        run: OddsIngestionRun,
        source_index: int,
        raw_payload: RawOddsPayload,
        checksum: str,
        errors: list[dict[str, Any]],
    ) -> OddsIngestionItemResult:
        """Persist a malformed or unresolved source payload as auditable raw evidence."""
        raw_payload.validation_status = RawOddsPayloadStatus.INVALID
        raw_payload.validation_errors = errors
        raw_payload.processed_at = datetime.now(UTC)
        run.failed_count += 1
        changes: dict[str, Any] = {"source_index": source_index, "validation_errors": errors}
        self.repository.add_audit(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            fixture_id=None,
            provider_name=run.provider_name,
            provider_fixture_id=raw_payload.provider_fixture_id,
            outcome=OddsAuditOutcome.VALIDATION_FAILED,
            checksum=checksum,
            changes=changes,
            snapshots_created=0,
            snapshots_ignored=0,
            movements_detected=0,
        )
        self.repository.add_outbox_event(
            ingestion_run_id=run.id,
            raw_payload_id=raw_payload.id,
            event_type=MarketDataEventType.ODDS_VALIDATION_FAILED,
            event_key_suffix="validation-failed",
            payload={
                "run_id": str(run.id),
                "provider": run.provider_name,
                "fixture_provider": raw_payload.fixture_provider_name,
                "provider_fixture_id": raw_payload.provider_fixture_id,
                "raw_payload_id": str(raw_payload.id),
                "validation_errors": errors,
            },
        )
        logger.warning(
            "market_data.odds_validation_failed",
            extra={
                "extra_fields": {
                    "run_id": str(run.id),
                    "provider": run.provider_name,
                    "raw_payload_id": str(raw_payload.id),
                    "error_count": len(errors),
                }
            },
        )
        return OddsIngestionItemResult(
            source_index=source_index,
            outcome=OddsAuditOutcome.VALIDATION_FAILED,
            snapshots_created=0,
            snapshots_ignored=0,
            movements_detected=0,
            validation_errors=errors,
        )
