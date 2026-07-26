from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.risk.enums import RiskRunStatus, RiskValidationStatus


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class RiskRunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    consensus_run_id: UUID
    parameters: dict[str, object] = Field(default_factory=dict)
    random_seed: int = Field(ge=0, le=2_147_483_647)


class RiskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    consensus_run_id: UUID
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    parameters: dict[str, object]
    random_seed: int
    status: RiskRunStatus
    input_checksum: str
    created_at: datetime


class RiskOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    risk_run_id: UUID
    fixture_id: UUID
    market_type: str
    outcome: str
    overall_risk_score: Decimal
    uncertainty_score: Decimal
    stability_score: Decimal
    calibration_risk: Decimal
    agreement_risk: Decimal
    data_quality_risk: Decimal
    completeness_score: Decimal
    components: dict[str, object]
    created_at: datetime


class RiskLineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    risk_run_id: UUID
    consensus_run_id: UUID
    probability_run_ids: list[str]
    dataset_snapshot_id: UUID
    feature_set_version_id: UUID
    parameters_checksum: str
    random_seed: int
    created_at: datetime


class RiskValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    risk_run_id: UUID
    rule_name: str
    status: RiskValidationStatus
    message: str
    created_at: datetime


class AnalyzerMetadataRead(BaseModel):
    identifier: str
    description: str
