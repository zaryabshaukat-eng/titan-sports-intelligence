"""Plugin registry and immutable specifications for feature-generation implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.feature_store.enums import FeatureDataType, FeatureType, MissingValuePolicy


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Declarative metadata for one versioned feature definition."""

    feature_id: str
    name: str
    description: str
    version: str
    owner: str
    source_modules: tuple[str, ...]
    dependencies: tuple[str, ...]
    calculation_logic: str
    feature_type: FeatureType
    data_type: FeatureDataType
    missing_value_policy: MissingValuePolicy
    validity_window_seconds: int | None = None


class FeatureGenerator(Protocol):
    """Plugin boundary: generators receive canonical source access, never provider JSON."""

    name: str
    generator_version: str

    @property
    def specs(self) -> tuple[FeatureSpec, ...]: ...

    async def generate(self, context: object) -> list[object]: ...


class FeatureGeneratorRegistry:
    """Explicit registry preserves a reviewable inventory and avoids implicit discovery."""

    def __init__(self) -> None:
        self._generators: dict[str, FeatureGenerator] = {}

    def register(self, generator: FeatureGenerator) -> None:
        if generator.name in self._generators:
            raise ValueError(f"Feature generator '{generator.name}' is already registered.")
        self._generators[generator.name] = generator

    @property
    def generators(self) -> tuple[FeatureGenerator, ...]:
        return tuple(self._generators[name] for name in sorted(self._generators))

    @property
    def specs(self) -> tuple[FeatureSpec, ...]:
        return tuple(spec for generator in self.generators for spec in generator.specs)


def build_default_registry() -> FeatureGeneratorRegistry:
    """Build TITAN's initial small, deterministic canonical-data-only generator portfolio."""
    from app.modules.feature_store.feature_sets.fixture import FixtureStatisticsGenerator
    from app.modules.feature_store.feature_sets.market import MarketSummaryGenerator
    from app.modules.feature_store.feature_sets.temporal import TemporalFeatureGenerator

    registry = FeatureGeneratorRegistry()
    for generator in (
        TemporalFeatureGenerator(),
        FixtureStatisticsGenerator(),
        MarketSummaryGenerator(),
    ):
        registry.register(generator)
    return registry
