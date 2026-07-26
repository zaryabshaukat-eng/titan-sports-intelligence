"""Append-only conversion of generator source references into durable lineage evidence."""

from __future__ import annotations

from uuid import UUID

from app.modules.feature_store.generator import SourceReference
from app.modules.feature_store.models import FeatureLineage


def build_lineage_rows(
    *,
    feature_value_id: UUID,
    sources: tuple[SourceReference, ...],
    calculation_logic: str,
    generator_version: str,
) -> list[FeatureLineage]:
    """Create one immutable lineage row per canonical dependency."""
    return [
        FeatureLineage(
            feature_value_id=feature_value_id,
            source_module=source.source_module,
            source_entity_type=source.source_entity_type,
            source_record_id=source.source_record_id,
            source_observed_at=source.observed_at,
            source_fingerprint=source.source_fingerprint,
            calculation_logic=calculation_logic,
            generator_version=generator_version,
        )
        for source in sources
    ]
