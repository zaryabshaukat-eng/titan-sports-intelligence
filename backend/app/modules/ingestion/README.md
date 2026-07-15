# Fixture Ingestion Pipeline

This bounded context imports provider fixture JSON into the canonical Sports Domain without adding provider-specific fields to `app/modules/sports`.

## Runtime flow

1. A protected internal caller submits `POST /api/v1/ingestion/fixtures/{provider_name}`.
2. The registered adapter validates its own DTOs and produces `NormalizedFixture`.
3. The pipeline records the original JSON, checksum, source provider, and idempotency key in `ingestion_raw_fixture_payloads`.
4. `CanonicalEntityResolver` resolves provider identities into canonical countries, leagues, competitions, seasons, teams, venues, timezones, and officials.
5. The service creates a canonical fixture, or updates only its explicitly mutable scheduling fields. A provider cannot change a known fixture's season or participants.
6. The transaction appends an audit record and an outbox event. A later delivery worker can publish the outbox event without losing it if the application stops after the database commit.

Validation failures are retained as raw payloads with structured errors, audit entries, and a `FixtureValidationFailed` outbox event. They do not create or mutate canonical Sports records.

## Reference adapter: `fixture_feed_v1`

The built-in reference adapter expects a payload shaped like this:

```json
{
  "fixture": {
    "id": "fixture-100",
    "kickoff": "2026-08-01T15:00:00+00:00",
    "status": "SCHEDULED",
    "timezone": "Europe/London"
  },
  "sport": "football",
  "country": { "id": "country-gb", "name": "United Kingdom", "iso_code": "GB" },
  "league": { "id": "league-100", "name": "English Football League" },
  "competition": { "id": "competition-100", "name": "Premier League", "type": "league" },
  "season": {
    "id": "season-2026",
    "name": "2026/27",
    "start_date": "2026-08-01",
    "end_date": "2027-05-31",
    "status": "planned"
  },
  "teams": {
    "home": { "id": "team-home", "name": "Home FC", "type": "club" },
    "away": { "id": "team-away", "name": "Away FC", "type": "club" }
  }
}
```

Optional venue and official fields are documented by the generated OpenAPI schema at `/docs` in development.

## Adding a second provider

1. Create `providers/<provider_name>.py` with provider-specific Pydantic request DTOs.
2. Implement `FixtureProviderAdapter.normalize()` and `extract_fixture_id()`.
3. Register the adapter in `providers/registry.py` application composition.
4. Add adapter unit tests using source JSON examples and verify only `NormalizedFixture` reaches the ingestion service.

Do not alter canonical Sports models, the resolver, or the ingestion service for provider vocabulary differences.
