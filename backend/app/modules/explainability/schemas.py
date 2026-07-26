from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.explainability.enums import ExplainabilityRunStatus, ExplainabilityValidationStatus


class ExplainabilityRunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    probability_run_id: UUID
    consensus_run_id: UUID
    risk_run_id: UUID
    parameters: dict[str, object] = Field(default_factory=dict)


class ExplainabilityRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    probability_run_id: UUID
    consensus_run_id: UUID
    risk_run_id: UUID
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    parameters: dict[str, object]
    status: ExplainabilityRunStatus
    input_checksum: str
    created_at: datetime


class ExplanationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explainability_run_id: UUID
    fixture_id: UUID
    market_type: str
    outcome: str
    explanation_summary: str
    confidence: Decimal
    evidence_completeness: Decimal
    traceability_score: Decimal
    coverage_score: Decimal
    created_at: datetime


class FeatureContributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explanation_id: UUID
    feature_id: str
    feature_value: Decimal | None
    contribution: Decimal
    direction: str
    source_feature_value_id: UUID
    created_at: datetime


class EvidenceReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explanation_id: UUID
    sequence: int
    source_type: str
    source_id: str
    description: str
    created_at: datetime


class ReasoningStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explanation_id: UUID
    position: int
    stage: str
    description: str
    source_type: str
    source_id: str
    created_at: datetime


class ExplainabilityLineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explainability_run_id: UUID
    probability_run_id: UUID
    consensus_run_id: UUID
    risk_run_id: UUID
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    research_experiment_id: UUID
    parameters_checksum: str
    created_at: datetime


class ExplainabilityValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    explainability_run_id: UUID
    rule_name: str
    status: ExplainabilityValidationStatus
    message: str
    created_at: datetime


class ExplainerMetadataRead(BaseModel):
    identifier: str
    description: str
