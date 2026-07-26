from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.evaluation.enums import BacktestRunStatus, BacktestValidationStatus, ScenarioType


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class HistoricalOutcome(BaseModel):
    probability_output_id: UUID
    observed_outcome: bool


class BacktestRunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    research_experiment_id: UUID
    probability_run_id: UUID
    consensus_run_id: UUID
    risk_run_id: UUID
    explainability_run_id: UUID
    scenario: ScenarioType
    parameters: dict[str, object] = Field(default_factory=dict)
    random_seed: int = Field(ge=0, le=2_147_483_647)
    outcomes: list[HistoricalOutcome] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def require_unique_outputs(self) -> BacktestRunCreate:
        """Prevent ambiguous replay labels for one immutable probability output."""
        identifiers = [item.probability_output_id for item in self.outcomes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Each probability output may appear only once in a backtest.")
        return self


class BacktestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    research_experiment_id: UUID
    probability_run_id: UUID
    consensus_run_id: UUID
    risk_run_id: UUID
    explainability_run_id: UUID
    scenario: ScenarioType
    parameters: dict[str, object]
    random_seed: int
    status: BacktestRunStatus
    input_checksum: str
    created_at: datetime


class BacktestResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    backtest_run_id: UUID
    probability_output_id: UUID
    fixture_id: UUID
    market_type: str
    outcome: str
    predicted_probability: Decimal
    observed_outcome: bool
    prediction_timestamp: datetime
    fixture_start_at: datetime
    created_at: datetime


class BacktestMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    backtest_run_id: UUID
    sample_count: int
    metrics: dict[str, object]
    reliability: list[dict[str, object]]
    created_at: datetime


class BacktestLineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    backtest_run_id: UUID
    parameters_checksum: str
    artifact_ids: dict[str, str]
    created_at: datetime


class BacktestValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    backtest_run_id: UUID
    rule_name: str
    status: BacktestValidationStatus
    message: str
    created_at: datetime


class ScenarioMetadataRead(BaseModel):
    identifier: str
    description: str


class BacktestComparisonRead(BaseModel):
    baseline_backtest_run_id: UUID
    candidate_backtest_run_id: UUID
    metric_deltas: dict[str, float]
