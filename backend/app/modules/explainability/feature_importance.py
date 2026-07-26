from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID


class FeatureImportanceRow(Protocol):
    """The immutable numeric fields required by a feature contribution engine."""

    @property
    def feature_id(self) -> str: ...

    @property
    def numeric_value(self) -> Decimal | None: ...

    @property
    def source_feature_value_id(self) -> UUID: ...


@dataclass(frozen=True, slots=True)
class Contribution:
    feature_id: str
    feature_value: Decimal | None
    contribution: Decimal
    direction: str
    source_feature_value_id: UUID


def deterministic(rows: Sequence[FeatureImportanceRow]) -> list[Contribution]:
    numeric = [(row, row.numeric_value) for row in rows if row.numeric_value is not None]
    denominator = sum((abs(value) for _, value in numeric), Decimal("0")) or Decimal("1")
    return [
        Contribution(
            row.feature_id,
            value,
            Decimal(str(abs(value) / denominator)),
            "positive" if value >= 0 else "negative",
            row.source_feature_value_id,
        )
        for row, value in numeric
    ]
