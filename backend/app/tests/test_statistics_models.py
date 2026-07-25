from app.modules.statistics.models import StatisticSnapshot

def test_statistic_snapshot_exposes_immutable_provenance_columns() -> None:
    columns = StatisticSnapshot.__table__.c
    assert {"raw_payload_id", "ingestion_run_id", "checksum", "observed_at", "values"} <= set(
        columns.keys()
    )
