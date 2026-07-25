# Statistics Ingestion

Statistics is an isolated bounded context. It depends on canonical fixtures imported by Fixture Ingestion and resolves teams against the Sports Domain, but owns statistic categories, versioned schemas, player identities, raw payloads, audit evidence, and immutable snapshots.

`StatisticSnapshot` is append-only. A correction or later observation creates another snapshot; no historical row is updated. `StatisticVersion` preserves the provider/category schema that interpreted each series, so Feature Engineering can select a known category/version/time window without relying on mutable provider semantics.

The read-only API is versioned below `/api/v1/statistics`: categories, fixture statistics, team statistics, player statistics, latest observations, and historical observations. Ingestion is protected at `POST /api/v1/statistics/ingestion/{provider_name}`.
