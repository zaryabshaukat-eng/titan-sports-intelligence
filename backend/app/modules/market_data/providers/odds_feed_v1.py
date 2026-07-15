"""Reference adapter for the documented ``odds_feed_v1`` source-provider contract."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.market_data.exceptions import OddsPayloadValidationError
from app.modules.market_data.providers.base import OddsProviderAdapter
from app.modules.market_data.schemas import (
    NormalizedBookmaker,
    NormalizedMarket,
    NormalizedOddsPayload,
    NormalizedSelection,
)


class OddsFeedV1FixtureReference(BaseModel):
    """Provider fixture reference, decoupled from the odds source's own registry name."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    provider: str = Field(min_length=1, max_length=64)
    id: str = Field(min_length=1, max_length=128)


class OddsFeedV1Bookmaker(BaseModel):
    """Provider bookmaker vocabulary."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    website_url: str | None = Field(default=None, max_length=512)


class OddsFeedV1MarketType(BaseModel):
    """Source market-type vocabulary mapped to canonical MarketType rows."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class OddsFeedV1Selection(BaseModel):
    """Source selection price vocabulary."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    key: str = Field(min_length=1, max_length=96)
    name: str = Field(min_length=1, max_length=160)
    decimal_odds: Decimal = Field(gt=Decimal("1"), max_digits=12, decimal_places=6)
    attributes: dict[str, Any] = Field(default_factory=dict)


class OddsFeedV1Market(BaseModel):
    """Source market vocabulary, including complete-set semantics for removal detection."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=128)
    market_type: OddsFeedV1MarketType
    status: str = Field(min_length=1, max_length=32)
    period: str = Field(default="full_time", min_length=1, max_length=32)
    line: Decimal | None = Field(default=None, max_digits=12, decimal_places=4)
    attributes: dict[str, Any] = Field(default_factory=dict)
    selections_complete: bool = True
    selections: list[OddsFeedV1Selection] = Field(min_length=1, max_length=100)


class OddsFeedV1Payload(BaseModel):
    """Complete reference source payload for one bookmaker and fixture at one observation time."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    fixture: OddsFeedV1FixtureReference
    bookmaker: OddsFeedV1Bookmaker
    observed_at: datetime
    markets: list[OddsFeedV1Market] = Field(min_length=1, max_length=100)


_STATUS_MAP: dict[str, str] = {
    "open": "open",
    "active": "open",
    "suspended": "suspended",
    "paused": "suspended",
    "closed": "closed",
    "settled": "settled",
}


def _validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Convert Pydantic details into a stable, raw-payload audit-safe format."""
    return [
        {
            "path": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors(include_input=False)
    ]


class OddsFeedV1Adapter(OddsProviderAdapter):
    """Normalize the reference odds feed without exposing source fields to core services."""

    provider_name = "odds_feed_v1"

    def extract_fixture_reference(self, payload: dict[str, Any]) -> tuple[str | None, str | None]:
        """Best-effort fixture identity retained even if the rest of a payload is invalid."""
        fixture = payload.get("fixture")
        if not isinstance(fixture, dict):
            return None, None
        provider = fixture.get("provider")
        fixture_id = fixture.get("id")
        normalized_provider = str(provider).lower() if provider is not None else None
        normalized_id = str(fixture_id) if fixture_id is not None else None
        if normalized_provider is not None and not 1 <= len(normalized_provider) <= 64:
            normalized_provider = None
        if normalized_id is not None and not 1 <= len(normalized_id) <= 128:
            normalized_id = None
        return normalized_provider, normalized_id

    def normalize(self, payload: dict[str, Any]) -> NormalizedOddsPayload:
        """Validate source JSON then map terminology into the canonical Market Data contract."""
        try:
            source = OddsFeedV1Payload.model_validate(payload)
            markets = [
                NormalizedMarket(
                    provider_id=market.id,
                    market_type_code=market.market_type.code,
                    market_type_name=market.market_type.name,
                    market_type_description=market.market_type.description,
                    status_code=_STATUS_MAP[market.status.lower()],
                    period_code=market.period,
                    line_value=market.line,
                    attributes=market.attributes,
                    selections_complete=market.selections_complete,
                    selections=[
                        NormalizedSelection(
                            provider_id=selection.id,
                            selection_key=selection.key,
                            name=selection.name,
                            decimal_odds=selection.decimal_odds,
                            attributes=selection.attributes,
                        )
                        for selection in market.selections
                    ],
                )
                for market in source.markets
            ]
            return NormalizedOddsPayload(
                fixture_provider_name=source.fixture.provider,
                provider_fixture_id=source.fixture.id,
                bookmaker=NormalizedBookmaker(
                    provider_id=source.bookmaker.id,
                    name=source.bookmaker.name,
                    code=source.bookmaker.code,
                    website_url=source.bookmaker.website_url,
                ),
                observed_at=source.observed_at,
                markets=markets,
            )
        except KeyError as exc:
            raise OddsPayloadValidationError(
                [
                    {
                        "path": "markets.status",
                        "message": f"unsupported provider market status '{exc.args[0]}'",
                        "type": "unsupported_market_status",
                    }
                ]
            ) from exc
        except ValidationError as exc:
            raise OddsPayloadValidationError(_validation_errors(exc)) from exc
        except ValueError as exc:
            raise OddsPayloadValidationError(
                [{"path": "normalization", "message": str(exc), "type": "normalization_error"}]
            ) from exc
