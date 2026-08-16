from app.modules.statistics.enums import RawStatisticPayloadStatus, StatisticsRunStatus
from app.modules.statistics.models import (
    RawStatisticPayload,
    StatisticIngestionRun,
    StatisticSnapshot,
)


def test_statistic_snapshot_exposes_immutable_provenance_columns() -> None:
    columns = StatisticSnapshot.__table__.c
    assert {"raw_payload_id", "ingestion_run_id", "checksum", "observed_at", "values"} <= set(
        columns.keys()
    )


def test_statistics_ingestion_run_status_uses_existing_postgresql_enum_values() -> None:
    """Bind StrEnum values, rather than member names, to the existing database enum."""
    enum_type = StatisticIngestionRun.__table__.c.status.type

    assert enum_type.name == "statistics_run_status"
    assert enum_type.enums == [status.value for status in StatisticsRunStatus]


def test_raw_statistic_payload_status_uses_existing_postgresql_enum_values() -> None:
    """Bind raw statistic payload StrEnum values to the existing database enum."""
    enum_type = RawStatisticPayload.__table__.c.validation_status.type

    assert enum_type.name == "statistics_raw_payload_status"
    assert enum_type.enums == [status.value for status in RawStatisticPayloadStatus]
