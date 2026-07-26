from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Contribution:
    feature_id: str
    feature_value: Decimal | None
    contribution: Decimal
    direction: str
    source_feature_value_id: object


def deterministic(rows: list[object]) -> list[Contribution]:
    numeric = [row for row in rows if row.numeric_value is not None]
    denominator = sum(abs(Decimal(str(row.numeric_value))) for row in numeric) or Decimal("1")
    return [
        Contribution(
            row.feature_id,
            row.numeric_value,
            Decimal(str(abs(Decimal(str(row.numeric_value))) / denominator)),
            "positive" if Decimal(str(row.numeric_value)) >= 0 else "negative",
            row.source_feature_value_id,
        )
        for row in numeric
    ]
