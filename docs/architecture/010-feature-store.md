# Feature Store & Feature Engineering

## Boundary

The Feature Store is TITAN's provider-neutral bridge from completed Data Layer bounded contexts to future research and intelligence modules. It owns feature definitions, immutable Feature Set versions, deterministic generation runs, generated values, lineage, and validation evidence. It does not own fixtures, statistics, odds, provider adapters, model training, or recommendations.

Generators read only canonical `sports`, `statistics`, and `market_data` tables. Raw provider payloads and provider identifiers are deliberately outside the boundary.

## Versioning and reproducibility

`FeatureSet` is a durable named catalog. Every `FeatureSetVersion` records a version, generator version, source modules, and a checksum of all definitions. A `FeatureDefinition` records the feature ID/version, owner, description, dependencies, calculation logic, type, data type, missing-value policy, and validity interval.

The service executes against a required timezone-aware `as_of` timestamp. It fingerprints the Feature Set definition and each immutable canonical source record. The Feature Set version, target fixture, cutoff, and source fingerprint form the generation idempotency key. Equal inputs return the existing run; a later immutable source observation causes a distinct append-only run, preserving historical reproduction.

## Data model

- `feature_store_feature_sets` and `feature_store_feature_set_versions`: metadata contract selected by future experiments and models.
- `feature_store_feature_definitions`: immutable individual feature metadata.
- `feature_store_generation_runs`: input fingerprint, status, retry-safe idempotency key, and audit timing.
- `feature_store_feature_values`: append-only values with canonical fixture/team/player/competition/season filters, quality score, exact numeric projection, calculation time, observation time, and validity window.
- `feature_store_lineage`: source module, canonical source record, source fingerprint, logic, and generator version for every generated value.
- `feature_store_validation_records`: persisted null/type/range/dependency/temporal/version validation outcomes.

No row is updated to correct historical feature data. PostgreSQL rejects direct update/delete operations on Feature Set versions, definitions, values, lineage, and validation evidence. A corrected upstream observation produces a new immutable run/value with independent lineage.

## Initial plugin portfolio

The explicit registry contains three deterministic generators:

- Temporal/team context: rest days plus recent home/away fixture counts.
- Fixture statistics: snapshot availability, possession, shots, discipline totals, and shots momentum delta.
- Market summary: current snapshot count, implied probability mean, and volatility.

Travel distance, result-derived form, and richer player features are not simulated. They will be introduced only after their canonical inputs exist, as new Feature Set versions and plugins.

## Interfaces

- `POST /api/v1/feature-store/generations` performs protected internal/offline generation (`research:execute`).
- `GET /api/v1/feature-store/feature-sets`, `/feature-sets/{code}/versions`, and the versioned
  `/definitions` route expose immutable registry metadata.
- `GET /api/v1/feature-store/features` filters values by canonical fixture, team, player, competition, season, timestamp, Feature Set version, and feature ID.
- `GET /api/v1/feature-store/features/{id}/lineage` and `/validation` expose the evidence required by downstream explainability and governance layers.

All retrieval contracts require `data:read`; no frontend route or provider-specific API is introduced.
