"""Versioned internal API contracts for Feature Store generation and retrieval."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.feature_store.enums import (
    FeatureDataType,
    FeatureType,
    GenerationStatus,
    MissingValuePolicy,
    ValidationStatus,
)


class PaginationParams(BaseModel):
    """Bounded offset pagination for internal feature retrieval endpoints."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class FeatureGenerationRequest(BaseModel):
    """Offline generation request; as-of time makes historical rebuilds deterministic."""

    feature_set_code: str = Field(default="core_fixture", pattern=r"^[a-z0-9_]+$")
    feature_set_version: str = Field(default="1.0.0", min_length=1, max_length=64)
    fixture_id: UUID
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("as_of must include a timezone offset")
        return value


class FeatureGenerationResult(BaseModel):
    """Compact result for an idempotent offline generation request."""

    generation_run_id: UUID
    status: GenerationStatus
    generated_count: int
    reused_existing_run: bool = False


class FeatureValueFilters(BaseModel):
    """Provider-neutral query controls covering all supported canonical subject identities."""

    fixture_id: UUID | None = None
    team_id: UUID | None = None
    player_id: UUID | None = None
    competition_id: UUID | None = None
    season_id: UUID | None = None
    feature_set_code: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$")
    feature_set_version: str | None = Field(default=None, min_length=1, max_length=64)
    feature_id: str | None = Field(default=None, min_length=1, max_length=128)
    observed_after: datetime | None = None
    observed_before: datetime | None = None

    @field_validator("observed_after", "observed_before")
    @classmethod
    def require_aware_filters(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timestamp filters must include a timezone offset")
        return value


class Page[T](BaseModel):
    """Uniform, documented page envelope for immutable Feature Store records."""

    items: list[T]
    total: int
    limit: int
    offset: int


class FeatureSetRead(BaseModel):
    """Stable Feature Set metadata, independent from a particular version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str
    owner: str
    created_at: datetime


class FeatureSetVersionRead(BaseModel):
    """Immutable version metadata required by downstream training and analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    feature_set_id: UUID
    version: str
    generator_version: str
    definition_checksum: str
    source_modules: list[str]
    created_at: datetime


class FeatureDefinitionRead(BaseModel):
    """Feature metadata explaining semantics, ownership, dependencies, and null policy."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    feature_set_version_id: UUID
    feature_id: str
    name: str
    description: str
    version: str
    owner: str
    source_modules: list[str]
    dependencies: list[str]
    calculation_logic: str
    feature_type: FeatureType
    data_type: FeatureDataType
    missing_value_policy: MissingValuePolicy
    validity_window_seconds: int | None
    created_at: datetime


class FeatureValueRead(BaseModel):
    """Immutable generated value with its reproducibility timestamps and quality assessment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generation_run_id: UUID
    feature_definition_id: UUID
    fixture_id: UUID | None
    team_id: UUID | None
    player_id: UUID | None
    competition_id: UUID | None
    season_id: UUID | None
    value: object | None
    numeric_value: Decimal | None
    quality_score: Decimal
    calculated_at: datetime
    observed_at: datetime
    valid_from: datetime
    valid_until: datetime | None
    created_at: datetime


class FeatureLineageRead(BaseModel):
    """Read contract for the canonical source records and logic behind one feature value."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    feature_value_id: UUID
    source_module: str
    source_entity_type: str
    source_record_id: UUID
    source_observed_at: datetime | None
    source_fingerprint: str | None
    calculation_logic: str
    generator_version: str
    created_at: datetime


class FeatureValidationRead(BaseModel):
    """Read contract for generated-feature quality-gate evidence."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    generation_run_id: UUID
    feature_definition_id: UUID
    feature_value_id: UUID | None
    rule_name: str
    status: ValidationStatus
    message: str
    created_at: datetime
