"""Pydantic API contracts for immutable consensus computation and evidence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.consensus.enums import (
    ConsensusRunStatus,
    ConsensusStrategy,
    ConsensusValidationStatus,
)


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class ConsensusRunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    probability_run_ids: list[UUID] = Field(min_length=2, max_length=50)
    strategy: ConsensusStrategy
    parameters: dict[str, object] = Field(default_factory=dict)
    random_seed: int = Field(ge=0, le=2_147_483_647)

    @model_validator(mode="after")
    def unique_inputs(self) -> ConsensusRunCreate:
        if len(self.probability_run_ids) != len(set(self.probability_run_ids)):
            raise ValueError("probability_run_ids must be unique")
        return self


class ConsensusRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    feature_set_version_id: UUID
    dataset_snapshot_id: UUID
    strategy: ConsensusStrategy
    parameters: dict[str, object]
    random_seed: int
    status: ConsensusRunStatus
    input_checksum: str
    created_at: datetime


class ConsensusOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    consensus_run_id: UUID
    fixture_id: UUID
    market_type: str
    outcome: str
    consensus_probability: Decimal
    confidence_score: Decimal
    disagreement_score: Decimal
    agreement_level: str
    confidence_metrics: dict[str, object]
    disagreement_metrics: dict[str, object]
    contributor_count: int
    expected_count: int
    created_at: datetime


class ConsensusLineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    consensus_run_id: UUID
    feature_set_version_id: UUID
    dataset_snapshot_id: UUID
    probability_run_ids: list[str]
    model_versions: list[dict[str, str]]
    calibration_versions: list[str]
    research_experiment_ids: list[str]
    parameters_checksum: str
    random_seed: int
    created_at: datetime


class ConsensusValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    consensus_run_id: UUID
    rule_name: str
    status: ConsensusValidationStatus
    message: str
    created_at: datetime


class StrategyMetadataRead(BaseModel):
    identifier: str
    description: str
    parameter_schema: dict[str, object]


class ConsensusMetricRead(BaseModel):
    fixture_id: UUID
    market_type: str
    outcome: str
    metrics: dict[str, object]
