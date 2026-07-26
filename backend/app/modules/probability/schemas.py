"""Pydantic contracts for immutable Probability Engine runs and audit evidence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.probability.enums import (
    CalibrationMethod,
    ProbabilityRunStatus,
    ProbabilityValidationStatus,
)


class PaginationParams(BaseModel):
    """Bounded pagination shared by Probability Engine collection endpoints."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    """Stable paginated collection contract."""

    items: list[T]
    total: int
    limit: int
    offset: int


class CalibrationVersionCreate(BaseModel):
    """A reviewed immutable calibration configuration."""

    calibration_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    version: str = Field(min_length=1, max_length=64)
    method: CalibrationMethod
    parameters: dict[str, object] = Field(default_factory=dict)
    compatible_model_identifiers: list[str] = Field(default_factory=list, max_length=50)
    owner: str = Field(min_length=1, max_length=128)

    @field_validator("compatible_model_identifiers")
    @classmethod
    def validate_unique_models(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("compatible_model_identifiers must not contain duplicates")
        if any(not identifier or len(identifier) > 96 for identifier in value):
            raise ValueError("each compatible model identifier must be between 1 and 96 characters")
        return value


class ProbabilityRunCreate(BaseModel):
    """Deterministic inference request over one immutable research dataset."""

    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    research_experiment_id: UUID
    model_identifier: str = Field(min_length=1, max_length=96)
    model_version: str = Field(min_length=1, max_length=64)
    calibration_version_id: UUID | None = None
    market_type: str = Field(min_length=1, max_length=96)
    outcome: str = Field(min_length=1, max_length=96)
    parameters: dict[str, object] = Field(default_factory=dict)
    random_seed: int = Field(ge=0, le=2_147_483_647)
    prediction_timestamp: datetime

    @field_validator("prediction_timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("prediction_timestamp must include a timezone offset")
        return value


class EvaluationSample(BaseModel):
    """Observed binary result supplied for evaluation of one immutable output."""

    probability_output_id: UUID
    observed_outcome: bool


class ProbabilityEvaluationCreate(BaseModel):
    """Evaluation request that records exactly which immutable estimates were assessed."""

    evaluation_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    samples: list[EvaluationSample] = Field(min_length=1, max_length=10_000)
    reliability_bins: int = Field(default=10, ge=2, le=100)

    @model_validator(mode="after")
    def reject_duplicate_outputs(self) -> ProbabilityEvaluationCreate:
        output_ids = [sample.probability_output_id for sample in self.samples]
        if len(output_ids) != len(set(output_ids)):
            raise ValueError("each probability output can appear once in an evaluation")
        return self


class CalibrationVersionRead(BaseModel):
    """Public metadata needed to reproduce calibration."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    calibration_code: str
    version: str
    method: CalibrationMethod
    parameters: dict[str, object]
    compatible_model_identifiers: list[str]
    owner: str
    created_at: datetime


class ProbabilityRunRead(BaseModel):
    """Immutable run metadata and terminal validation status."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_code: str
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    research_experiment_id: UUID
    model_identifier: str
    model_version: str
    calibration_version_id: UUID | None
    market_type: str
    outcome: str
    parameters: dict[str, object]
    random_seed: int
    prediction_timestamp: datetime
    status: ProbabilityRunStatus
    input_checksum: str
    created_at: datetime


class ProbabilityOutputRead(BaseModel):
    """One auditable calibrated probability estimate, never a recommendation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    probability_run_id: UUID
    fixture_id: UUID
    market_type: str
    outcome: str
    estimated_probability: Decimal
    confidence_interval_low: Decimal
    confidence_interval_high: Decimal
    calibration_version: str | None
    prediction_timestamp: datetime
    support_count: int
    created_at: datetime


class ProbabilityEvaluationRead(BaseModel):
    """Persisted aggregate metric evidence for one immutable probability run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    probability_run_id: UUID
    evaluation_code: str
    sample_count: int
    metrics: dict[str, object]
    reliability: list[dict[str, object]]
    input_checksum: str
    created_at: datetime


class ProbabilityLineageRead(BaseModel):
    """All versions and checksums required to replay a probability run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    probability_run_id: UUID
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    research_experiment_id: UUID
    model_identifier: str
    model_version: str
    calibration_version: str | None
    parameters_checksum: str
    random_seed: int
    created_at: datetime


class ProbabilityValidationRead(BaseModel):
    """Persisted compatibility evidence for a ProbabilityRun."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    probability_run_id: UUID
    rule_name: str
    status: ProbabilityValidationStatus
    message: str
    created_at: datetime


class ModelMetadataRead(BaseModel):
    """Registry metadata for a baseline or future trainable inference model."""

    model_identifier: str
    version: str
    algorithm: str
    description: str
    parameter_schema: dict[str, object]
