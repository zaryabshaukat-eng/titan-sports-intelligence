"""Pydantic contracts for immutable dataset snapshots, experiments, hypotheses, and results."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.research.enums import (
    AnalysisType,
    ExperimentStatus,
    HypothesisDecision,
    ValidationStatus,
)


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class DatasetSelection(BaseModel):
    """Frozen Feature Store selection, not a live query at experiment execution."""

    feature_ids: list[str] = Field(min_length=1, max_length=100)
    fixture_id: UUID | None = None
    team_id: UUID | None = None
    player_id: UUID | None = None
    competition_id: UUID | None = None
    season_id: UUID | None = None
    observed_after: datetime | None = None
    observed_before: datetime | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> DatasetSelection:
        if (
            self.observed_after
            and self.observed_before
            and self.observed_after > self.observed_before
        ):
            raise ValueError("observed_after must be earlier than observed_before")
        for timestamp in (self.observed_after, self.observed_before):
            if timestamp and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError("dataset selection timestamps must include timezone offsets")
        return self


class DatasetSnapshotCreate(BaseModel):
    dataset_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    owner: str = Field(min_length=1, max_length=128)
    feature_set_version_id: UUID
    selection: DatasetSelection


class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType
    feature_id: str = Field(min_length=1, max_length=128)
    related_feature_id: str | None = Field(default=None, min_length=1, max_length=128)
    bins: int = Field(default=10, ge=2, le=50)

    @model_validator(mode="after")
    def validate_analysis_dependencies(self) -> AnalysisRequest:
        if self.analysis_type in {AnalysisType.CORRELATION, AnalysisType.SIGNIFICANCE}:
            if self.related_feature_id is None:
                raise ValueError(
                    "related_feature_id is required for correlation and significance analysis"
                )
            if self.related_feature_id == self.feature_id:
                raise ValueError("related_feature_id must differ from feature_id")
        return self


class ExperimentCreate(BaseModel):
    experiment_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    owner: str = Field(min_length=1, max_length=128)
    feature_set_version_id: UUID
    dataset_snapshot_id: UUID
    random_seed: int = Field(ge=0, le=2_147_483_647)
    analysis: AnalysisRequest
    parameters: dict[str, object] = Field(default_factory=dict)


class HypothesisCreate(BaseModel):
    hypothesis_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    statement: str = Field(min_length=1, max_length=4000)
    description: str | None = Field(default=None, max_length=4000)
    owner: str = Field(min_length=1, max_length=128)


class HypothesisEvaluationCreate(BaseModel):
    hypothesis_id: UUID
    experiment_id: UUID
    statistic_result_id: UUID | None = None
    result: str = Field(min_length=1, max_length=4000)
    evidence: dict[str, object] = Field(default_factory=dict)
    statistical_significance: bool | None = None
    p_value: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    decision: HypothesisDecision


class DatasetSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_code: str
    version: str
    name: str
    description: str
    owner: str
    feature_set_version_id: UUID
    selection: dict[str, object]
    generator_versions: dict[str, str]
    source_value_count: int
    checksum: str
    created_at: datetime


class DatasetSnapshotRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_snapshot_id: UUID
    source_feature_value_id: UUID
    feature_definition_id: UUID
    feature_id: str
    fixture_id: UUID | None
    team_id: UUID | None
    player_id: UUID | None
    competition_id: UUID | None
    season_id: UUID | None
    value: object | None
    numeric_value: Decimal | None
    observed_at: datetime
    calculated_at: datetime


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_code: str
    name: str
    description: str
    owner: str
    feature_set_version_id: UUID
    dataset_snapshot_id: UUID
    generator_versions: dict[str, str]
    parameters: dict[str, object]
    random_seed: int
    status: ExperimentStatus
    input_checksum: str
    created_at: datetime


class StatisticResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    result_key: str
    analysis_type: AnalysisType
    feature_id: str
    related_feature_id: str | None
    method: str
    values: dict[str, object]
    numeric_value: Decimal | None
    sample_size: int
    confidence_interval_low: Decimal | None
    confidence_interval_high: Decimal | None
    p_value: Decimal | None
    created_at: datetime


class HypothesisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hypothesis_code: str
    statement: str
    description: str | None
    owner: str
    created_at: datetime


class HypothesisEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hypothesis_id: UUID
    experiment_id: UUID
    statistic_result_id: UUID | None
    result: str
    evidence: dict[str, object]
    statistical_significance: bool | None
    p_value: Decimal | None
    decision: HypothesisDecision
    created_at: datetime


class ExperimentLineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    generator_versions: dict[str, str]
    parameters_checksum: str
    random_seed: int
    created_at: datetime


class ExperimentValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    rule_name: str
    status: ValidationStatus
    message: str
    created_at: datetime
