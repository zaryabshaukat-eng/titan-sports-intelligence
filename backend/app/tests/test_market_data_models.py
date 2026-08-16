"""Unit tests for Market Data persistence metadata and immutable-history safeguards."""

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from app.modules.market_data.enums import OddsIngestionRunStatus, RawOddsPayloadStatus
from app.modules.market_data.models import (
    Market,
    MarketDataOutboxEvent,
    MarketProviderMapping,
    OddsIngestionRun,
    OddsMovement,
    OddsSnapshot,
    RawOddsPayload,
    Selection,
)
from app.shared.persistence.base import Base


def test_market_data_models_configure_with_sports_and_ingestion_boundaries() -> None:
    """Market Data references canonical records without changing their model definitions."""
    configure_mappers()

    assert "market_data_odds_snapshots" in Base.metadata.tables
    assert Market.__mapper__.relationships["selections"].uselist is True
    assert OddsSnapshot.__mapper__.relationships["selection"].uselist is False
    assert OddsMovement.__mapper__.relationships["previous_snapshot"].uselist is False
    assert MarketDataOutboxEvent.__mapper__.relationships["raw_payload"].uselist is False


def test_market_data_models_define_immutable_snapshot_and_identity_constraints() -> None:
    """Database constraints prevent duplicate observations and provider identity mappings."""
    snapshot_uniques = {
        constraint.name
        for constraint in OddsSnapshot.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    mapping_uniques = {
        constraint.name
        for constraint in MarketProviderMapping.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    snapshot_checks = {
        constraint.name
        for constraint in OddsSnapshot.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "uq_market_data_odds_snapshots_observation" in snapshot_uniques
    assert "uq_market_data_provider_mappings_provider_entity" in mapping_uniques
    assert "ck_market_data_odds_snapshots_decimal_odds" in snapshot_checks
    assert "market_data_raw_odds_payloads" in Base.metadata.tables
    assert Selection.__tablename__ == "market_data_selections"
    assert RawOddsPayload.__tablename__ == "market_data_raw_odds_payloads"


def test_odds_ingestion_run_status_uses_existing_postgresql_enum_values() -> None:
    """Bind StrEnum values, rather than member names, to the existing database enum."""
    enum_type = OddsIngestionRun.__table__.c.status.type

    assert enum_type.name == "market_data_odds_ingestion_run_status"
    assert enum_type.enums == [status.value for status in OddsIngestionRunStatus]


def test_raw_odds_payload_status_uses_existing_postgresql_enum_values() -> None:
    """Bind raw odds payload StrEnum values to the existing database enum."""
    enum_type = RawOddsPayload.__table__.c.validation_status.type

    assert enum_type.name == "market_data_raw_odds_payload_status"
    assert enum_type.enums == [status.value for status in RawOddsPayloadStatus]
