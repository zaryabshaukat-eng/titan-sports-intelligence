"""Deterministic contribution and reasoning coverage for Explainability."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.explainability.confidence import scores
from app.modules.explainability.feature_importance import deterministic
from app.modules.explainability.reasoning import chain


@dataclass(frozen=True)
class FeatureRow:
    feature_id: str
    numeric_value: Decimal | None
    source_feature_value_id: UUID


def test_deterministic_contributions_reasoning_and_confidence_are_reproducible() -> None:
    rows = [
        FeatureRow(feature_id="shots", numeric_value=Decimal("3"), source_feature_value_id=uuid4()),
        FeatureRow(
            feature_id="fouls", numeric_value=Decimal("-1"), source_feature_value_id=uuid4()
        ),
    ]
    contributions = deterministic(rows)
    assert sum(item.contribution for item in contributions) == Decimal("1")
    assert (
        contributions[1].direction == "negative"
        and len(
            chain(dataset_id=uuid4(), probability_id=uuid4(), consensus_id=uuid4(), risk_id=uuid4())
        )
        == 5
    )
    confidence, evidence, traceability, coverage = scores(evidence_count=5, contribution_count=2)
    assert confidence > 0 and evidence == traceability == 1 and coverage == 0.4
