"""Provider-neutral resolution of odds entities into canonical Market Data and Sports records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.models import FixtureProviderIdentity
from app.modules.market_data.enums import MarketProviderEntityType
from app.modules.market_data.exceptions import OddsPayloadValidationError
from app.modules.market_data.models import (
    Bookmaker,
    Market,
    MarketStatus,
    MarketType,
    Selection,
)
from app.modules.market_data.repositories import MarketDataIngestionRepository
from app.modules.market_data.schemas import (
    NormalizedBookmaker,
    NormalizedMarket,
    NormalizedOddsPayload,
    NormalizedSelection,
)
from app.modules.sports.models import Fixture


@dataclass(frozen=True, slots=True)
class ResolvedMarket:
    """Market resolution result including status-transition information for movement tracking."""

    market: Market
    was_created: bool
    previous_status: MarketStatus | None
    status_applied: bool


@dataclass(frozen=True, slots=True)
class ResolvedSelection:
    """Selection resolution result including whether it is new or returning to the market."""

    selection: Selection
    was_added_or_reactivated: bool


class MarketDataEntityResolver:
    """Resolve provider IDs without introducing provider fields into canonical domain tables."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        repository: MarketDataIngestionRepository,
        provider_name: str,
    ) -> None:
        self.session = session
        self.repository = repository
        self.provider_name = provider_name

    async def resolve_fixture(self, payload: NormalizedOddsPayload) -> Fixture:
        """Resolve provider fixture identity through Market Data first, then Fixture Ingestion."""
        mapping = await self.repository.get_mapping(
            payload.fixture_provider_name,
            MarketProviderEntityType.FIXTURE,
            payload.provider_fixture_id,
        )
        if mapping is not None:
            fixture = await self.session.get(Fixture, mapping.canonical_entity_id)
            if fixture is not None:
                return fixture
            raise self._broken_mapping_error("fixture", payload.provider_fixture_id)

        fixture_identity = await self.session.scalar(
            select(FixtureProviderIdentity).where(
                FixtureProviderIdentity.provider_name == payload.fixture_provider_name,
                FixtureProviderIdentity.provider_fixture_id == payload.provider_fixture_id,
            )
        )
        if fixture_identity is None:
            raise OddsPayloadValidationError(
                [
                    {
                        "path": "fixture",
                        "message": "provider fixture is not present in the canonical Sports Domain",
                        "type": "unresolved_fixture",
                    }
                ]
            )
        fixture = await self.session.get(Fixture, fixture_identity.fixture_id)
        if fixture is None:
            raise self._broken_mapping_error("fixture", payload.provider_fixture_id)
        await self.repository.link_mapping(
            provider_name=payload.fixture_provider_name,
            entity_type=MarketProviderEntityType.FIXTURE,
            provider_entity_id=payload.provider_fixture_id,
            canonical_entity_id=fixture.id,
        )
        return fixture

    async def resolve_bookmaker(self, value: NormalizedBookmaker) -> Bookmaker:
        """Resolve a bookmaker by provider ID, code, then conservative name matching."""
        mapped = await self._mapped_entity(
            self.provider_name, MarketProviderEntityType.BOOKMAKER, value.provider_id, Bookmaker
        )
        if mapped is not None:
            return mapped

        bookmaker = None
        if value.code is not None:
            bookmaker = await self.session.scalar(
                select(Bookmaker).where(Bookmaker.code == value.code)
            )
        if bookmaker is None:
            bookmaker = await self.session.scalar(
                select(Bookmaker).where(func.lower(Bookmaker.name) == value.name.lower())
            )
        if bookmaker is None:
            bookmaker = Bookmaker(
                name=value.name,
                code=value.code,
                website_url=value.website_url,
            )
            self.session.add(bookmaker)
            await self.session.flush()
        await self.repository.link_mapping(
            provider_name=self.provider_name,
            entity_type=MarketProviderEntityType.BOOKMAKER,
            provider_entity_id=value.provider_id,
            canonical_entity_id=bookmaker.id,
        )
        return bookmaker

    async def resolve_market(
        self,
        *,
        fixture_id: UUID,
        value: NormalizedMarket,
        observed_at: datetime,
    ) -> ResolvedMarket:
        """Resolve a market and apply a newer provider status without rewriting historical movements."""
        market_type = await self._resolve_market_type(value)
        incoming_status = await self._resolve_market_status(value.status_code)
        mapped = await self._mapped_entity(
            self.provider_name, MarketProviderEntityType.MARKET, value.provider_id, Market
        )
        market_created = False
        if mapped is not None:
            self._validate_market_identity(mapped, fixture_id, market_type.id, value)
            market = mapped
        else:
            market = await self.session.scalar(
                select(Market).where(
                    Market.fixture_id == fixture_id,
                    Market.market_type_id == market_type.id,
                    Market.period_code == value.period_code,
                    Market.line_key == value.line_key,
                )
            )
            if market is None:
                market = Market(
                    fixture_id=fixture_id,
                    market_type_id=market_type.id,
                    market_status_id=incoming_status.id,
                    period_code=value.period_code,
                    line_value=value.line_value,
                    line_key=value.line_key,
                    attributes=value.attributes,
                    status_observed_at=observed_at,
                )
                self.session.add(market)
                await self.session.flush()
                market_created = True
            await self.repository.link_mapping(
                provider_name=self.provider_name,
                entity_type=MarketProviderEntityType.MARKET,
                provider_entity_id=value.provider_id,
                canonical_entity_id=market.id,
            )

        if market_created:
            return ResolvedMarket(
                market=market,
                was_created=True,
                previous_status=None,
                status_applied=True,
            )

        current_status = await self.session.get(MarketStatus, market.market_status_id)
        if current_status is None:
            raise self._broken_mapping_error("market status", value.status_code)
        if observed_at < market.status_observed_at:
            return ResolvedMarket(
                market=market,
                was_created=False,
                previous_status=current_status,
                status_applied=False,
            )
        if current_status.id != incoming_status.id:
            market.market_status_id = incoming_status.id
            market.status_observed_at = observed_at
            return ResolvedMarket(
                market=market,
                was_created=False,
                previous_status=current_status,
                status_applied=True,
            )
        market.status_observed_at = observed_at
        return ResolvedMarket(
            market=market,
            was_created=False,
            previous_status=current_status,
            status_applied=True,
        )

    async def resolve_selection(
        self, market_id: UUID, value: NormalizedSelection
    ) -> ResolvedSelection:
        """Resolve a selection identity and reactivate it when a provider lists it again."""
        mapped = await self._mapped_entity(
            self.provider_name, MarketProviderEntityType.SELECTION, value.provider_id, Selection
        )
        selection_added_or_reactivated = False
        if mapped is not None:
            if mapped.market_id != market_id:
                raise OddsPayloadValidationError(
                    [
                        {
                            "path": "selection",
                            "message": "provider selection identity resolves to a different canonical market",
                            "type": "selection_market_conflict",
                        }
                    ]
                )
            selection = mapped
            if not selection.is_active:
                selection.is_active = True
                selection.removed_at = None
                selection_added_or_reactivated = True
        else:
            selection = await self.session.scalar(
                select(Selection).where(
                    Selection.market_id == market_id,
                    Selection.selection_key == value.selection_key,
                )
            )
            if selection is None:
                selection = Selection(
                    market_id=market_id,
                    selection_key=value.selection_key,
                    name=value.name,
                    attributes=value.attributes,
                )
                self.session.add(selection)
                await self.session.flush()
                selection_added_or_reactivated = True
            elif not selection.is_active:
                selection.is_active = True
                selection.removed_at = None
                selection_added_or_reactivated = True
        await self.repository.link_mapping(
            provider_name=self.provider_name,
            entity_type=MarketProviderEntityType.SELECTION,
            provider_entity_id=value.provider_id,
            canonical_entity_id=selection.id,
        )
        return ResolvedSelection(
            selection=selection,
            was_added_or_reactivated=selection_added_or_reactivated,
        )

    async def _resolve_market_type(self, value: NormalizedMarket) -> MarketType:
        """Create future market types as data rather than requiring a schema migration."""
        market_type = await self.session.scalar(
            select(MarketType).where(MarketType.code == value.market_type_code)
        )
        if market_type is None:
            market_type = MarketType(
                code=value.market_type_code,
                name=value.market_type_name,
                description=value.market_type_description,
            )
            self.session.add(market_type)
            await self.session.flush()
        return market_type

    async def _resolve_market_status(self, status_code: str) -> MarketStatus:
        """Resolve only configured market statuses; source-provider status mapping is adapter-owned."""
        market_status = await self.session.scalar(
            select(MarketStatus).where(MarketStatus.code == status_code)
        )
        if market_status is None:
            raise OddsPayloadValidationError(
                [
                    {
                        "path": "markets.status",
                        "message": f"canonical market status '{status_code}' is not configured",
                        "type": "unknown_market_status",
                    }
                ]
            )
        return market_status

    async def _mapped_entity[EntityT](
        self,
        provider_name: str,
        entity_type: MarketProviderEntityType,
        provider_entity_id: str,
        entity_class: type[EntityT],
    ) -> EntityT | None:
        """Load a mapped canonical object and reject dangling external identity links."""
        mapping = await self.repository.get_mapping(provider_name, entity_type, provider_entity_id)
        if mapping is None:
            return None
        entity = await self.session.get(entity_class, mapping.canonical_entity_id)
        if entity is None:
            raise self._broken_mapping_error(entity_type.value, provider_entity_id)
        return entity

    @staticmethod
    def _validate_market_identity(
        market: Market, fixture_id: UUID, market_type_id: UUID, value: NormalizedMarket
    ) -> None:
        """Prevent a source market identity from being silently repointed to a new canonical market."""
        if (
            market.fixture_id != fixture_id
            or market.market_type_id != market_type_id
            or market.period_code != value.period_code
            or market.line_key != value.line_key
        ):
            raise OddsPayloadValidationError(
                [
                    {
                        "path": "market",
                        "message": "provider market identity conflicts with immutable canonical market identity",
                        "type": "market_identity_conflict",
                    }
                ]
            )

    @staticmethod
    def _broken_mapping_error(entity_type: str, provider_entity_id: str) -> OddsPayloadValidationError:
        """Create a consistent audit-safe error for dangling external-to-canonical links."""
        return OddsPayloadValidationError(
            [
                {
                    "path": "entity_resolution",
                    "message": (
                        f"provider {entity_type} identity '{provider_entity_id}' points to "
                        "a missing canonical record"
                    ),
                    "type": "broken_provider_mapping",
                }
            ]
        )
