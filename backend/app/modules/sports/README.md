# Canonical Sports Domain

This bounded context contains provider-neutral sports reference data and read-only REST adapters. It deliberately does not contain provider payloads, ingestion logic, statistics, predictions, recommendations, or machine-learning code.

## Semantics

- **League** is a durable sporting organization or hierarchy, optionally tied to a country.
- **Competition** is a specific league, cup, tournament, playoff, friendly, or other competition. It can optionally belong to a League and/or Country.
- **Season** belongs to exactly one Competition.
- **Fixture** belongs to exactly one Season. The Competition is therefore obtained through `Fixture → Season → Competition`, avoiding inconsistent duplicated competition IDs.
- **Fixture Status** is an extensible canonical taxonomy. The initial migration seeds scheduled, delayed, postponed, live, halftime, finished, cancelled, and abandoned states.
- **Fixture Status History** is append-only, allowing operational status transitions to be audited without overwriting history.

Master records—Country, League, Competition, Season, Team, Venue, and Official—support soft deletion. Fixtures are not soft deleted: a cancellation or abandonment is represented by canonical status instead, preserving historical truth.
