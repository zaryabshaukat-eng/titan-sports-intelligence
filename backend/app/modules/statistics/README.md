# Statistics Ingestion Platform

Phase 2.3.4 stores provider-neutral fixture, team, and player statistics as immutable observations. A source payload is retained first, normalized by its adapter, resolved to existing fixtures and teams, then appended as `StatisticSnapshot` rows with run, checksum, audit, and transactional-outbox provenance.

The reference `statistics_feed_v1` payload uses `fixture`, `observed_at`, and `statistics`; each statistic has a `scope`, a `{code, name}` category, and arbitrary JSON `values`. This accommodates possession, xG, goalkeeper measures, minutes, and future provider metrics without schema changes.

To add a provider, implement `StatisticsProviderAdapter`, add its source DTOs, register it in `providers/registry.py`, and add mapping tests. The resolver and persistence service remain unchanged.
