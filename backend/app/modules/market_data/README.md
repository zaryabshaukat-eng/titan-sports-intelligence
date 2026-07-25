# Market Data & Odds Ingestion

This bounded context implements Phase 2.3.3: immutable bookmaker odds history, market lifecycle tracking, and provider-neutral ingestion. It does not implement consensus pricing, probability estimation, recommendations, or any other intelligence engine.

## Ingestion flow

1. An authenticated internal caller submits `POST /api/v1/market-data/ingestion/odds/{provider_name}`.
2. The source adapter validates provider DTOs and emits `NormalizedOddsPayload`.
3. The original JSON, source checksum, idempotency key, validation outcome, and fixture reference are stored in `market_data_raw_odds_payloads`.
4. The resolver links the fixture to the identity established by Fixture Ingestion, and resolves bookmaker, market, selection, and provider mappings.
5. A changed decimal price creates a new immutable `OddsSnapshot`; an unchanged price is counted and audited without writing a duplicate snapshot.
6. The service appends price, opening, closing, suspension, reopening, selection-added, and selection-removed `OddsMovement` rows as appropriate.
7. The same transaction appends an audit row and transactional-outbox events for later delivery.

Validation failures retain the raw payload, structured errors, audit record, and `OddsValidationFailed` event. They never create fixtures.

## Reference adapter: `odds_feed_v1`

The built-in reference adapter expects one bookmaker/fixture observation:

```json
{
  "fixture": { "provider": "fixture_feed_v1", "id": "fixture-100" },
  "bookmaker": { "id": "bookmaker-100", "name": "TITAN Sportsbook", "code": "titan" },
  "observed_at": "2026-08-01T12:00:00+00:00",
  "markets": [
    {
      "id": "market-1x2",
      "market_type": { "code": "match_winner", "name": "Match Winner" },
      "status": "open",
      "period": "full_time",
      "selections_complete": true,
      "selections": [
        { "id": "home", "key": "home", "name": "Home", "decimal_odds": "1.80" },
        { "id": "draw", "key": "draw", "name": "Draw", "decimal_odds": "3.50" },
        { "id": "away", "key": "away", "name": "Away", "decimal_odds": "4.20" }
      ]
    }
  ]
}
```

`fixture.provider` and `fixture.id` must resolve to a canonical fixture previously imported through Phase 2.3.2. This prevents odds feeds from fabricating sports fixtures.

## Immutability and movement rules

- `market_data_odds_snapshots` has no update path. Each changed price gets a new row with provider, bookmaker, fixture, market, selection, decimal odds, implied probability, observation time, run, raw payload, and checksum.
- The same exact raw payload is idempotently ignored through its provider-namespaced checksum key.
- A repeated price at a later observation is audited as ignored; it does not create artificial price movement.
- New price snapshots are compared with the nearest prior snapshot for that provider, bookmaker, and selection to record opening, increase, or decrease movements.
- A transition to `closed` records the current latest prices as closing movements. `suspended` and `open` transitions generate their corresponding lifecycle movements and events.
- A complete market payload marks missing provider selection mappings as removed. Canonical selections and their historical snapshots are never deleted.

## Adding another provider

1. Create `providers/<provider_name>.py` with source-specific Pydantic DTOs.
2. Implement `OddsProviderAdapter.normalize()` and `extract_fixture_reference()`.
3. Register the adapter in `providers/registry.py`.
4. Add mapping and validation tests using provider payload examples.

The normalized service, resolver, immutable snapshot tables, and canonical Sports Domain do not change for a new provider.

## Read-only internal API

All endpoints are versioned under `/api/v1/market-data` and require bearer authentication:

- `GET /bookmakers`, `/market-types`, `/market-statuses`, `/markets`, and `/markets/{id}/selections`
- `GET /odds-snapshots`, `/odds-history`, and `/latest-odds`
- `GET /fixtures/{fixture_id}/odds`
- `GET /fixtures/{fixture_id}/markets/{market_id}/odds`
- `GET /movement-history`

The current authentication foundation fails closed until a real token verifier is configured. That is intentional: source data and market history must not become public by accident.
