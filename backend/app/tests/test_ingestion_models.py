"""Unit tests for ingestion persistence metadata and reproducibility constraints."""

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import configure_mappers

from app.modules.ingestion.models import (
    FixtureIngestionAudit,
    FixtureIngestionRun,
    FixtureProviderIdentity,
    IngestionOutboxEvent,
    ProviderEntityIdentity,
    RawFixturePayload,
)
from app.shared.persistence.base import Base


def test_ingestion_models_configure_with_sports_domain_relationships() -> None:
    """Ingestion provenance can reference canonical fixtures without changing Sports models."""
    configure_mappers()

    assert "ingestion_raw_fixture_payloads" in Base.metadata.tables
    assert FixtureProviderIdentity.__mapper__.relationships["latest_raw_payload"].uselist is False
    assert RawFixturePayload.__mapper__.relationships["audit_entries"].uselist is True
    assert IngestionOutboxEvent.__mapper__.relationships["raw_payload"].uselist is False


def test_ingestion_models_define_idempotency_and_provider_identity_constraints() -> None:
    """Database-level uniqueness prevents duplicate payload receipts and identity mappings."""
    raw_uniques = {
        constraint.name
        for constraint in RawFixturePayload.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    fixture_identity_uniques = {
        constraint.name
        for constraint in FixtureProviderIdentity.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "uq_ingestion_raw_fixture_payloads_provider_key" in raw_uniques
    assert "uq_ingestion_fixture_provider_identities_provider_fixture" in fixture_identity_uniques
    assert FixtureIngestionRun.__tablename__ == "ingestion_fixture_runs"
    assert FixtureIngestionAudit.__tablename__ == "ingestion_fixture_audit"
    assert ProviderEntityIdentity.__tablename__ == "ingestion_provider_entity_identities"
