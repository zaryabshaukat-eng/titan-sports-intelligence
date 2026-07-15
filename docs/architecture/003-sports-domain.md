# 003 — Canonical Sports Domain

**Status:** Implemented in Phase 2.3.1  
**Last updated:** 2026-07-15

The Sports Domain is canonical and provider-neutral. It represents the sporting world TITAN reasons about, rather than data-provider payloads.

## Core relationships

```text
Country --< CountryTimezone >-- Timezone
Country --< League --< Competition --< Season --< Fixture
Country --< Team >-- Venue
Fixture >-- Team (home)
Fixture >-- Team (away)
Fixture >-- FixtureStatus
Fixture --< FixtureStatusHistory >-- FixtureStatus
Fixture --< FixtureOfficial >-- Official
```

## Key semantics

- A League is a durable sporting organization or hierarchy.
- A Competition is a league, cup, tournament, playoff, friendly, or other contest, optionally related to a League and Country.
- A Season belongs to one Competition.
- A Fixture belongs to one Season; competition identity is reached through the season, avoiding inconsistent duplicate foreign keys.
- CountryTimezone permits multiple IANA timezones per country and restricts each country to one primary timezone.
- FixtureStatus is an extensible canonical taxonomy. FixtureStatusHistory records transitions append-only.

## Read API

All Sports endpoints are GET-only under `/api/v1/sports`. List resources provide validated filters and offset pagination, with a maximum page size of 100.

The domain intentionally excludes provider IDs, raw payloads, odds, statistics, predictions, models, and recommendations.
