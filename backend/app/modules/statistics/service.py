"""Orchestrates auditable, retry-safe append-only statistics ingestion."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.statistics.enums import (
    RawStatisticPayloadStatus,
    StatisticsAuditOutcome,
    StatisticsEventType,
    StatisticsRunStatus,
)
from app.modules.statistics.exceptions import (
    StatisticsConflictError,
    StatisticsError,
    StatisticsPayloadValidationError,
    StatisticsPersistenceError,
    StatisticsResolutionError,
)
from app.modules.statistics.models import (
    RawStatisticPayload,
    StatisticAudit,
    StatisticIngestionRun,
    StatisticSnapshot,
    StatisticsOutboxEvent,
)
from app.modules.statistics.providers.base import StatisticsProviderAdapter
from app.modules.statistics.repositories import StatisticsRepository
from app.modules.statistics.schemas import IngestionItemRead, StatisticsIngestionResult

logger = get_logger(__name__)


class StatisticsIngestionService:
    def __init__(self, session: AsyncSession, provider_adapter: StatisticsProviderAdapter) -> None:
        self.session, self.adapter, self.repository = (
            session,
            provider_adapter,
            StatisticsRepository(session),
        )

    async def ingest(self, payloads: list[dict[str, object]]) -> StatisticsIngestionResult:
        provider = await self.repository.provider(self.adapter.provider_name)
        run = StatisticIngestionRun(
            provider_id=provider.id,
            status=StatisticsRunStatus.RUNNING,
            received_count=len(payloads),
        )
        self.session.add(run)
        await self.session.flush()
        results: list[IngestionItemRead] = []
        for index, payload in enumerate(payloads):
            results.append(await self._one(provider.id, run, index, payload))
        run.completed_at = datetime.now(UTC)
        run.status = (
            StatisticsRunStatus.COMPLETED_WITH_ERRORS
            if run.failed_count
            else StatisticsRunStatus.COMPLETED
        )
        return StatisticsIngestionResult(
            run_id=run.id, provider=self.adapter.provider_name, items=results
        )

    async def _one(
        self,
        provider_id: Any,
        run: StatisticIngestionRun,
        index: int,
        payload: dict[str, object],
    ) -> IngestionItemRead:
        checksum = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        raw, is_new = await self._create_raw_payload_once(
            run=run,
            provider_id=provider_id,
            checksum=checksum,
            payload=payload,
        )
        if not is_new:
            return IngestionItemRead(
                source_index=index, outcome=StatisticsAuditOutcome.UNCHANGED, snapshots_created=0
            )
        canonical_writes_started = False
        try:
            normalized = self._normalize(payload)
            raw.fixture_provider_name = normalized.fixture.provider
            raw.provider_fixture_id = normalized.fixture.id
            fixture = await self.repository.fixture(
                normalized.fixture.provider, normalized.fixture.id
            )
            if fixture is None:
                raise StatisticsResolutionError(
                    "Fixture must already exist through Fixture Ingestion."
                )
            provider = await self.repository.provider(self.adapter.provider_name)
            canonical_writes_started = True
            async with self.session.begin_nested():
                created = await self._append_snapshots(
                    provider_id=provider_id,
                    run=run,
                    raw=raw,
                    fixture_id=fixture,
                    observed_at=normalized.observed_at,
                    checksum=checksum,
                    observations=normalized.statistics,
                    provider=provider,
                )
        except StatisticsError as exc:
            return self._record_validation_failure(
                run,
                index,
                raw,
                checksum,
                self._errors(exc),
                rolled_back=canonical_writes_started,
            )
        except IntegrityError:
            return self._record_validation_failure(
                run,
                index,
                raw,
                checksum,
                self._errors(
                    StatisticsPersistenceError("A concurrent statistics write conflicted.")
                ),
                rolled_back=canonical_writes_started,
            )
        else:
            raw.canonical_fixture_id = fixture
            raw.validation_status = RawStatisticPayloadStatus.VALID
            raw.validation_status, raw.processed_at = (
                RawStatisticPayloadStatus.APPLIED,
                datetime.now(UTC),
            )
            run.snapshots_created_count += created
            outcome = (
                StatisticsAuditOutcome.PROCESSED if created else StatisticsAuditOutcome.UNCHANGED
            )
            self.session.add(
                StatisticAudit(
                    ingestion_run_id=run.id,
                    raw_payload_id=raw.id,
                    provider_id=provider_id,
                    outcome=outcome,
                    checksum=checksum,
                    changes={"snapshots_created": created},
                )
            )
            event = StatisticsEventType.INGESTED if created else StatisticsEventType.UPDATED
            self.session.add(
                StatisticsOutboxEvent(
                    ingestion_run_id=run.id,
                    raw_payload_id=raw.id,
                    event_type=event,
                    event_key=f"{run.id}:{raw.id}",
                    payload={
                        "fixture_id": str(fixture),
                        "snapshots_created": created,
                        "provider": self.adapter.provider_name,
                    },
                )
            )
            return IngestionItemRead(source_index=index, outcome=outcome, snapshots_created=created)

    async def _create_raw_payload_once(
        self,
        *,
        run: StatisticIngestionRun,
        provider_id: Any,
        checksum: str,
        payload: dict[str, object],
    ) -> tuple[RawStatisticPayload, bool]:
        """Persist immutable evidence once, handling concurrent idempotent retries safely."""
        existing = await self.session.scalar(
            select(RawStatisticPayload).where(
                RawStatisticPayload.provider_id == provider_id,
                RawStatisticPayload.idempotency_key == checksum,
            )
        )
        if existing is not None:
            return existing, False

        raw = RawStatisticPayload(
            ingestion_run_id=run.id,
            provider_id=provider_id,
            checksum=checksum,
            idempotency_key=checksum,
            payload=payload,
            validation_status=RawStatisticPayloadStatus.RECEIVED,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(raw)
                await self.session.flush()
        except IntegrityError as exc:
            existing = await self.session.scalar(
                select(RawStatisticPayload).where(
                    RawStatisticPayload.provider_id == provider_id,
                    RawStatisticPayload.idempotency_key == checksum,
                )
            )
            if existing is not None:
                return existing, False
            raise StatisticsConflictError(
                "A concurrent raw-payload write could not be resolved deterministically."
            ) from exc
        return raw, True

    def _normalize(self, payload: dict[str, object]):
        """Convert source validation errors into explicit audit-safe domain errors."""
        try:
            return self.adapter.normalize(payload)
        except ValidationError as exc:
            raise StatisticsPayloadValidationError(exc.errors()) from exc

    async def _append_snapshots(
        self,
        *,
        provider_id: Any,
        run: StatisticIngestionRun,
        raw: RawStatisticPayload,
        fixture_id: Any,
        observed_at: datetime,
        checksum: str,
        observations: list[Any],
        provider: Any,
    ) -> int:
        """Append an all-or-nothing payload's canonical observations inside a savepoint."""
        created = 0
        for observation in observations:
            series_id, refs = await self.repository.series(fixture_id, provider, observation)
            exists = await self.session.scalar(
                select(StatisticSnapshot.id).where(
                    StatisticSnapshot.provider_id == provider_id,
                    StatisticSnapshot.series_id == series_id,
                    StatisticSnapshot.observed_at == observed_at,
                    StatisticSnapshot.checksum == checksum,
                )
            )
            if exists is None:
                self.session.add(
                    StatisticSnapshot(
                        ingestion_run_id=run.id,
                        raw_payload_id=raw.id,
                        provider_id=provider_id,
                        fixture_id=fixture_id,
                        scope=observation.scope,
                        series_id=series_id,
                        values=observation.values,
                        observed_at=observed_at,
                        checksum=checksum,
                        **refs,
                    )
                )
                created += 1
        await self.session.flush()
        return created

    @staticmethod
    def _errors(exc: StatisticsError) -> list[dict[str, Any]]:
        """Return consistent structured error evidence without exposing tracebacks."""
        if isinstance(exc, StatisticsPayloadValidationError):
            return exc.errors
        return [{"code": exc.__class__.__name__, "message": str(exc)}]

    def _record_validation_failure(
        self,
        run: StatisticIngestionRun,
        index: int,
        raw: RawStatisticPayload,
        checksum: str,
        errors: list[dict[str, Any]],
        *,
        rolled_back: bool,
    ) -> IngestionItemRead:
        """Persist only raw payload and failure evidence after savepoint rollback."""
        raw.validation_status = RawStatisticPayloadStatus.INVALID
        raw.validation_errors = errors
        raw.processed_at = datetime.now(UTC)
        run.failed_count += 1
        self.session.add(
            StatisticAudit(
                ingestion_run_id=run.id,
                raw_payload_id=raw.id,
                provider_id=raw.provider_id,
                outcome=StatisticsAuditOutcome.VALIDATION_FAILED,
                checksum=checksum,
                changes={"source_index": index},
                error_details=errors,
            )
        )
        self.session.add(
            StatisticsOutboxEvent(
                ingestion_run_id=run.id,
                raw_payload_id=raw.id,
                event_type=StatisticsEventType.VALIDATION_FAILED,
                event_key=f"{run.id}:{raw.id}",
                payload={"source_index": index, "errors": errors},
            )
        )
        logger.warning(
            "statistics.payload_validation_failed",
            extra={
                "extra_fields": {
                    "provider": self.adapter.provider_name,
                    "fixture_provider": raw.fixture_provider_name,
                    "provider_fixture_id": raw.provider_fixture_id,
                    "payload_checksum": checksum,
                    "reason": errors,
                    "canonical_writes_rolled_back": rolled_back,
                }
            },
        )
        return IngestionItemRead(
            source_index=index,
            outcome=StatisticsAuditOutcome.VALIDATION_FAILED,
            validation_errors=errors,
        )
