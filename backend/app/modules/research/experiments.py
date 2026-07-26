"""Pure transformations from frozen dataset rows into deterministic analysis inputs."""

from __future__ import annotations

from decimal import Decimal

from app.modules.research.models import DatasetSnapshotRow


def numeric_analysis_inputs(
    rows: list[DatasetSnapshotRow],
) -> tuple[dict[str, list[float]], dict[str, dict[str, float]]]:
    """Project materialized rows into numeric series and deterministic canonical-subject pairs."""
    values: dict[str, list[float]] = {}
    keyed_values: dict[str, dict[str, float]] = {}
    for row in rows:
        if row.numeric_value is None:
            continue
        value = float(Decimal(str(row.numeric_value)))
        values.setdefault(row.feature_id, []).append(value)
        keyed_values.setdefault(row.feature_id, {})[_subject_key(row)] = value
    return values, keyed_values


def _subject_key(row: DatasetSnapshotRow) -> str:
    """Use a stable canonical subject key rather than a provider identity or row insertion order."""
    for attribute in ("fixture_id", "team_id", "player_id", "competition_id", "season_id"):
        identifier = getattr(row, attribute)
        if identifier is not None:
            return f"{attribute}:{identifier}"
    return f"row:{row.id}"
