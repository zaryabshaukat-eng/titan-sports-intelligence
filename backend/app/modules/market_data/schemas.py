"""Provider-neutral normalized odds contracts and public read models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.market_data.enums import OddsAuditOutcome, OddsMovementType


def market_line_key(line_value: Decimal | None) -> str:
    """Return a stable non-null natural-key component for optional market handicap/total lines."""
    if line_value is None:
        return "none"
    normalized = format(line_value.normalize(), "f")
    return "0" if normalized in {"-0", ""} else normalized


class NormalizedBookmaker(BaseModel):
    """Provider-neutral bookmaker identity and optional public metadata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    website_url: str | None = Field(default=None, max_length=512)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        """Store bookmaker codes as stable lowercase natural keys."""
        return value.lower() if value is not None else None


class NormalizedSelection(BaseModel):
    """Provider-neutral selection and decimal-price observation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider_id: str = Field(min_length=1, max_length=128)
    selection_key: str = Field(min_length=1, max_length=96)
    name: str = Field(min_length=1, max_length=160)
    decimal_odds: Decimal = Field(gt=Decimal("1"), max_digits=12, decimal_places=6)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("selection_key")
    @classmethod
    def normalize_selection_key(cls, value: str) -> str:
        """Normalize generic selection labels for canonical uniqueness comparisons."""
        return value.lower().replace(" ", "_")

    @property
    def implied_probability(self) -> Decimal:
        """Calculate the implied probability with stable precision for persistence."""
        return (Decimal("1") / self.decimal_odds).quantize(
            Decimal("0.00000001"), rounding=ROUND_HALF_UP
        )


class NormalizedMarket(BaseModel):
    """A complete provider view of one fixture market and its currently quoted selections."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider_id: str = Field(min_length=1, max_length=128)
    market_type_code: str = Field(min_length=1, max_length=64)
    market_type_name: str = Field(min_length=1, max_length=160)
    market_type_description: str | None = Field(default=None, max_length=2000)
    status_code: str = Field(min_length=1, max_length=32)
    period_code: str = Field(default="full_time", min_length=1, max_length=32)
    line_value: Decimal | None = Field(default=None, max_digits=12, decimal_places=4)
    attributes: dict[str, Any] = Field(default_factory=dict)
    selections_complete: bool = True
    selections: list[NormalizedSelection] = Field(min_length=1, max_length=100)

    @field_validator("market_type_code", "status_code", "period_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        """Use stable lowercase controlled keys for cross-provider canonical resolution."""
        return value.lower().replace(" ", "_")

    @model_validator(mode="after")
    def ensure_distinct_selections(self) -> NormalizedMarket:
        """Reject ambiguous provider markets before any persistent selection resolution."""
        provider_ids = [selection.provider_id for selection in self.selections]
        selection_keys = [selection.selection_key for selection in self.selections]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("market selection provider identities must be unique")
        if len(selection_keys) != len(set(selection_keys)):
            raise ValueError("market selection keys must be unique")
        return self

    @property
    def line_key(self) -> str:
        """Expose the canonical non-null key used to distinguish handicap and total markets."""
        return market_line_key(self.line_value)


class NormalizedOddsPayload(BaseModel):
    """Full provider-neutral odds payload prepared by an adapter for the ingestion service."""

    model_config = ConfigDict(str_strip_whitespace=True)

    fixture_provider_name: str = Field(min_length=1, max_length=64)
    provider_fixture_id: str = Field(min_length=1, max_length=128)
    bookmaker: NormalizedBookmaker
    observed_at: datetime
    markets: list[NormalizedMarket] = Field(min_length=1, max_length=100)

    @field_validator("fixture_provider_name")
    @classmethod
    def normalize_provider_name(cls, value: str) -> str:
        """Provider names are stable lowercase registry keys."""
        return value.lower()

    @field_validator("observed_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        """Reject timestamps that cannot be placed on an immutable odds timeline."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone offset")
        return value

    @model_validator(mode="after")
    def ensure_distinct_markets(self) -> NormalizedOddsPayload:
        """Prevent one raw payload from describing the same provider market twice."""
        provider_ids = [market.provider_id for market in self.markets]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("market provider identities must be unique within a payload")
        return self


class OddsIngestionRequest(BaseModel):
    """Protected internal request carrying source-provider JSON payloads."""

    payloads: list[dict[str, Any]] = Field(min_length=1, max_length=250)


class OddsIngestionItemResult(BaseModel):
    """Per-payload processing result without returning source-provider JSON."""

    source_index: int = Field(ge=0)
    outcome: OddsAuditOutcome
    fixture_id: UUID | None = None
    snapshots_created: int = Field(ge=0)
    snapshots_ignored: int = Field(ge=0)
    movements_detected: int = Field(ge=0)
    validation_errors: list[dict[str, Any]] | None = None


class OddsIngestionBatchResult(BaseModel):
    """Auditable aggregate result for an odds ingestion run."""

    run_id: UUID
    provider_name: str
    received_count: int = Field(ge=0)
    snapshots_created_count: int = Field(ge=0)
    snapshots_ignored_count: int = Field(ge=0)
    movements_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    items: list[OddsIngestionItemResult]


class ReadSchema(BaseModel):
    """Base API read schema supporting direct SQLAlchemy entity conversion."""

    model_config = ConfigDict(from_attributes=True)


class AuditReadSchema(ReadSchema):
    """Common identity and timestamps for Market Data API records."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class BookmakerRead(AuditReadSchema):
    name: str
    code: str | None
    website_url: str | None
    is_active: bool
    deleted_at: datetime | None


class MarketTypeRead(AuditReadSchema):
    code: str
    name: str
    description: str | None
    parameter_schema: dict[str, Any]
    is_active: bool


class MarketStatusRead(AuditReadSchema):
    code: str
    name: str
    description: str | None
    is_terminal: bool
    sort_order: int


class MarketRead(AuditReadSchema):
    fixture_id: UUID
    market_type_id: UUID
    market_status_id: UUID
    period_code: str
    line_value: Decimal | None
    line_key: str
    attributes: dict[str, Any]


class SelectionRead(AuditReadSchema):
    market_id: UUID
    selection_key: str
    name: str
    is_active: bool
    removed_at: datetime | None
    attributes: dict[str, Any]


class OddsSnapshotRead(AuditReadSchema):
    ingestion_run_id: UUID
    raw_payload_id: UUID
    provider_name: str
    bookmaker_id: UUID
    fixture_id: UUID
    market_id: UUID
    selection_id: UUID
    decimal_odds: Decimal
    implied_probability: Decimal
    observed_at: datetime
    checksum: str


class OddsMovementRead(AuditReadSchema):
    ingestion_run_id: UUID
    raw_payload_id: UUID
    bookmaker_id: UUID
    market_id: UUID
    selection_id: UUID | None
    previous_snapshot_id: UUID | None
    current_snapshot_id: UUID | None
    movement_type: OddsMovementType
    previous_decimal_odds: Decimal | None
    current_decimal_odds: Decimal | None
    delta_decimal_odds: Decimal | None
    observed_at: datetime
    details: dict[str, Any]


class Page[T](BaseModel):
    """Stable offset-pagination envelope for internal read-only Market Data APIs."""

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class PaginationParams(BaseModel):
    """Shared bounded pagination parameters."""

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookmakerFilters(BaseModel):
    """Read filters for bookmakers."""

    q: str | None = Field(default=None, min_length=1, max_length=160)
    is_active: bool | None = None


class MarketFilters(BaseModel):
    """Read filters for fixture-scoped canonical markets."""

    fixture_id: UUID | None = None
    market_type_id: UUID | None = None
    market_status_id: UUID | None = None
    period_code: str | None = Field(default=None, min_length=1, max_length=32)


class OddsSnapshotFilters(BaseModel):
    """Read filters for historical and fixture-market odds snapshots."""

    provider_name: str | None = Field(default=None, min_length=1, max_length=64)
    bookmaker_id: UUID | None = None
    fixture_id: UUID | None = None
    market_id: UUID | None = None
    selection_id: UUID | None = None
    observed_after: datetime | None = None
    observed_before: datetime | None = None

    @field_validator("observed_after", "observed_before")
    @classmethod
    def require_timezone_aware_bound(cls, value: datetime | None) -> datetime | None:
        """Avoid ambiguous historical-query boundaries."""
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("odds history bounds must include a timezone offset")
        return value

    @model_validator(mode="after")
    def validate_time_window(self) -> OddsSnapshotFilters:
        """Reject contradictory history filters before database access."""
        if self.observed_after and self.observed_before and self.observed_after > self.observed_before:
            raise ValueError("observed_after must be earlier than or equal to observed_before")
        return self


class OddsMovementFilters(BaseModel):
    """Read filters for market movement history."""

    bookmaker_id: UUID | None = None
    fixture_id: UUID | None = None
    market_id: UUID | None = None
    selection_id: UUID | None = None
    movement_type: OddsMovementType | None = None
    observed_after: datetime | None = None
    observed_before: datetime | None = None

    @field_validator("observed_after", "observed_before")
    @classmethod
    def require_timezone_aware_bound(cls, value: datetime | None) -> datetime | None:
        """Avoid ambiguous movement-history boundaries."""
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("movement history bounds must include a timezone offset")
        return value
