"""Orchestrates auditable, retry-safe append-only statistics ingestion."""

# ruff: noqa: E501, E701, E702
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.statistics.enums import (
    RawStatisticPayloadStatus,
    StatisticsAuditOutcome,
    StatisticsEventType,
    StatisticsRunStatus,
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
        self, provider_id: Any, run: StatisticIngestionRun, index: int, payload: dict[str, object]
    ) -> IngestionItemRead:
        checksum = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        fixture_provider, fixture_id = self.adapter.extract_fixture_reference(payload)
        existing = await self.session.scalar(
            select(RawStatisticPayload).where(
                RawStatisticPayload.provider_id == provider_id,
                RawStatisticPayload.idempotency_key == checksum,
            )
        )
        if existing:
            return IngestionItemRead(
                source_index=index, outcome=StatisticsAuditOutcome.UNCHANGED, snapshots_created=0
            )
        raw = RawStatisticPayload(
            ingestion_run_id=run.id,
            provider_id=provider_id,
            fixture_provider_name=fixture_provider,
            provider_fixture_id=fixture_id,
            checksum=checksum,
            idempotency_key=checksum,
            payload=payload,
            validation_status=RawStatisticPayloadStatus.RECEIVED,
        )
        self.session.add(raw)
        await self.session.flush()
        try:
            normalized = self.adapter.normalize(payload)
            fixture = await self.repository.fixture(
                normalized.fixture.provider, normalized.fixture.id
            )
            if fixture is None:
                raise ValueError("fixture must already exist through Fixture Ingestion")
            raw.canonical_fixture_id, raw.validation_status = (
                fixture,
                RawStatisticPayloadStatus.VALID,
            )
            created = 0
            for observation in normalized.statistics:
                series_id, refs = await self.repository.series(
                    fixture, await self.repository.provider(self.adapter.provider_name), observation
                )
                exists = await self.session.scalar(
                    select(StatisticSnapshot.id).where(
                        StatisticSnapshot.provider_id == provider_id,
                        StatisticSnapshot.series_id == series_id,
                        StatisticSnapshot.observed_at == normalized.observed_at,
                        StatisticSnapshot.checksum == checksum,
                    )
                )
                if exists is None:
                    self.session.add(
                        StatisticSnapshot(
                            ingestion_run_id=run.id,
                            raw_payload_id=raw.id,
                            provider_id=provider_id,
                            fixture_id=fixture,
                            scope=observation.scope,
                            series_id=series_id,
                            values=observation.values,
                            observed_at=normalized.observed_at,
                            checksum=checksum,
                            **refs,
                        )
                    )
                    created += 1
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
        except Exception as exc:
            raw.validation_status, raw.validation_errors, raw.processed_at = (
                RawStatisticPayloadStatus.INVALID,
                [{"message": str(exc)}],
                datetime.now(UTC),
            )
            run.failed_count += 1
            self.session.add(
                StatisticAudit(
                    ingestion_run_id=run.id,
                    raw_payload_id=raw.id,
                    provider_id=provider_id,
                    outcome=StatisticsAuditOutcome.VALIDATION_FAILED,
                    checksum=checksum,
                    changes={},
                    error_details=raw.validation_errors,
                )
            )
            self.session.add(
                StatisticsOutboxEvent(
                    ingestion_run_id=run.id,
                    raw_payload_id=raw.id,
                    event_type=StatisticsEventType.VALIDATION_FAILED,
                    event_key=f"{run.id}:{raw.id}",
                    payload={"errors": raw.validation_errors},
                )
            )
            return IngestionItemRead(
                source_index=index,
                outcome=StatisticsAuditOutcome.VALIDATION_FAILED,
                validation_errors=raw.validation_errors,
            )
