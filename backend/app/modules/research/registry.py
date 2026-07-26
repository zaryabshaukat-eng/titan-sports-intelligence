"""Explicit registry for supported deterministic statistical methods."""

from __future__ import annotations

from app.modules.research.enums import AnalysisType
from app.modules.research.statistics import (
    StatisticalResult,
    correlation,
    descriptive,
    distribution,
    welch_significance,
)


class AnalysisRegistry:
    """Maps reviewed analysis names to pure statistical primitives; it contains no ML algorithms."""

    def execute(
        self,
        *,
        analysis_type: AnalysisType,
        feature_id: str,
        related_feature_id: str | None,
        values: dict[str, list[float]],
        keyed_values: dict[str, dict[str, float]],
        bins: int,
    ) -> StatisticalResult:
        """Execute one provider-neutral analysis from materialized dataset values only."""
        primary = values.get(feature_id, [])
        if analysis_type is AnalysisType.DESCRIPTIVE:
            return descriptive(primary, feature_id=feature_id)
        if analysis_type is AnalysisType.DISTRIBUTION:
            return distribution(primary, feature_id=feature_id, bins=bins)
        assert related_feature_id is not None
        related = values.get(related_feature_id, [])
        if analysis_type is AnalysisType.CORRELATION:
            return correlation(
                keyed_values.get(feature_id, {}),
                keyed_values.get(related_feature_id, {}),
                left_feature=feature_id,
                right_feature=related_feature_id,
            )
        return welch_significance(
            primary,
            related,
            left_feature=feature_id,
            right_feature=related_feature_id,
        )
