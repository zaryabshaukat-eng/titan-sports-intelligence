# Feature Store

The Feature Store is a provider-neutral, append-only boundary between TITAN's canonical data layer and future research, model-training, probability, and evaluation services. It never reads raw provider payload tables. Its only source modules are canonical `sports`, `statistics`, and `market_data` records.

## Reproducibility and versions

`FeatureSet` is a stable named catalog. `FeatureSetVersion` snapshots its generator version, checksum, and source modules. `FeatureDefinition` contains the individual feature ID, version, owner, dependencies, calculation logic, type, data type, missing-value policy, and validity window.

The service first calculates source fingerprints at an explicit timezone-aware `as_of` cutoff. That input fingerprint, feature-set version, fixture, and cutoff form a unique idempotency key. An identical run is reused; changed immutable source records create a distinct generation run and append a new value history.

## Values, lineage, and validation

`FeatureValue` is append-only and holds the calculated/observation timestamps, validity interval, quality score, canonical subject IDs, exact numeric projection, and JSON value. `FeatureLineage` points to the target canonical fixture and every statistic snapshot or odds snapshot used, then records the calculation logic and generator version. `FeatureValidationRecord` persists null-policy, data-type, quality-range, dependency-provenance, temporal-boundary, and generator-version outcomes. PostgreSQL triggers reject updates and deletes for immutable feature metadata/evidence records.

## Built-in generators

The initial registry provides small deterministic reference generators:

- `temporal`: home/away rest days and home/away recent-fixture counts.
- `fixture_statistics`: snapshot availability, possession, shots, discipline totals, and a simple shots delta.
- `market_summary`: latest-snapshot count plus implied-probability mean and volatility.

They intentionally do not infer results, train models, or access provider payloads. Travel distance, rich form, and player features require canonical source data that is not yet present and should be added as new generator and feature-set versions, never by changing existing definitions.

## Operations

`POST /api/v1/feature-store/generations` is a protected internal/offline operation requiring `research:execute`. It is deterministic for a fixture and `as_of` timestamp. Read APIs require `data:read` and support canonical fixture, team, player, competition, season, timestamp, Feature Set version, and feature-ID filters. The versioned definitions endpoint exposes the metadata required to interpret a `FeatureValue`. Use lineage and validation endpoints with every downstream analytical result that consumes a feature value.
