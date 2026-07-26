"""Dataset snapshot construction helpers that copy immutable Feature Store values into Research."""

from __future__ import annotations

from uuid import UUID

from app.modules.feature_store.models import FeatureDefinition, FeatureValue
from app.modules.research.models import DatasetSnapshotRow


def build_snapshot_rows(
    *,
    dataset_snapshot_id: UUID,
    source_rows: list[tuple[FeatureValue, FeatureDefinition]],
) -> list[DatasetSnapshotRow]:
    """Copy selected Feature Store observations so research never uses a live source query."""
    return [
        DatasetSnapshotRow(
            dataset_snapshot_id=dataset_snapshot_id,
            source_feature_value_id=value.id,
            feature_definition_id=definition.id,
            feature_id=definition.feature_id,
            fixture_id=value.fixture_id,
            team_id=value.team_id,
            player_id=value.player_id,
            competition_id=value.competition_id,
            season_id=value.season_id,
            value=value.value,
            numeric_value=value.numeric_value,
            observed_at=value.observed_at,
            calculated_at=value.calculated_at,
        )
        for value, definition in source_rows
    ]
