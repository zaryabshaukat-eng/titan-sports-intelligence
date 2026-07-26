"""Market-summary generators over immutable canonical odds observations."""

from __future__ import annotations

from decimal import Decimal

from app.modules.feature_store.enums import FeatureDataType, FeatureType, MissingValuePolicy
from app.modules.feature_store.generator import (
    FeatureGenerationContext,
    GeneratedFeature,
    SourceReference,
)
from app.modules.feature_store.metadata import fingerprint
from app.modules.feature_store.registry import FeatureSpec


class MarketSummaryGenerator:
    """Generate explainable implied-probability summaries without interpreting betting outcomes."""

    name = "market_summary"
    generator_version = "1.0.0"

    @property
    def specs(self) -> tuple[FeatureSpec, ...]:
        return (
            FeatureSpec(
                "market_latest_snapshot_count",
                "Market latest snapshot count",
                "Number of canonical latest odds snapshots available at the generation cutoff.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "market_data"),
                ("market_data_odds_snapshots.fixture_id", "market_data_odds_snapshots.observed_at"),
                "count latest immutable odds snapshot per provider/bookmaker/selection",
                FeatureType.MARKET,
                FeatureDataType.INTEGER,
                MissingValuePolicy.ZERO,
                3600,
            ),
            FeatureSpec(
                "market_implied_probability_mean",
                "Market implied probability mean",
                "Arithmetic mean of current canonical implied probabilities "
                "across latest snapshots.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "market_data"),
                ("market_data_odds_snapshots.implied_probability",),
                "mean implied_probability across latest snapshots",
                FeatureType.MARKET,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
                3600,
            ),
            FeatureSpec(
                "market_implied_probability_volatility",
                "Market implied probability volatility",
                "Population standard deviation of latest canonical implied probabilities.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "market_data"),
                ("market_data_odds_snapshots.implied_probability",),
                "population standard deviation of latest implied_probability values",
                FeatureType.MARKET,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
                3600,
            ),
        )

    async def generate(self, context: object) -> list[object]:
        assert isinstance(context, FeatureGenerationContext)
        snapshots = await context.source_reader.latest_odds(
            fixture_id=context.fixture.fixture_id, as_of=context.as_of
        )
        probabilities = [Decimal(str(item.implied_probability)) for item in snapshots]
        mean = sum(probabilities, Decimal("0")) / len(probabilities) if probabilities else None
        variance = (
            sum((value - mean) ** 2 for value in probabilities) / len(probabilities)
            if mean is not None
            else None
        )
        volatility = variance.sqrt() if variance is not None else None
        sources = tuple(
            SourceReference(
                "market_data",
                "odds_snapshot",
                row.id,
                row.observed_at,
                fingerprint(
                    {
                        "id": row.id,
                        "observed_at": row.observed_at,
                        "checksum": row.checksum,
                    }
                ),
            )
            for row in snapshots
        )
        fixture = context.fixture
        shared = {
            "fixture_id": fixture.fixture_id,
            "competition_id": fixture.competition_id,
            "season_id": fixture.season_id,
        }
        return [
            GeneratedFeature(
                "market_latest_snapshot_count", len(snapshots), Decimal("1"), sources, **shared
            ),
            GeneratedFeature(
                "market_implied_probability_mean",
                mean,
                Decimal("1") if mean is not None else Decimal("0"),
                sources,
                **shared,
            ),
            GeneratedFeature(
                "market_implied_probability_volatility",
                volatility,
                Decimal("1") if volatility is not None else Decimal("0"),
                sources,
                **shared,
            ),
        ]
