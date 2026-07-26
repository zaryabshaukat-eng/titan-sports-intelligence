from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.evaluation_monitoring.enums import (
    AlertSeverity,
    MonitoringStatus,
    ValidationStatus,
)


class ProviderObservation(BaseModel):
    provider_name: str = Field(min_length=1, max_length=128)
    freshness_seconds: int = Field(ge=0)
    completeness_score: float = Field(ge=0, le=1)


class MonitoringRunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    backtest_run_id: UUID
    configuration_code: str = Field(default="default", min_length=1, max_length=96)
    configuration_version: str = Field(default="1", min_length=1, max_length=64)
    thresholds: dict[str, float] = Field(default_factory=dict)
    random_seed: int = Field(ge=0, le=2_147_483_647)
    providers: list[ProviderObservation] = Field(default_factory=list, max_length=100)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    backtest_run_id: UUID
    status: MonitoringStatus
    input_checksum: str
    created_at: datetime


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    evaluation_run_id: UUID
    created_at: datetime
    metric_name: str | None = None
    value: float | None = None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    evaluation_run_id: UUID
    severity: AlertSeverity
    alert_type: str
    message: str
    evidence: dict[str, object]
    created_at: datetime


class ValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    evaluation_run_id: UUID
    rule_name: str
    status: ValidationStatus
    message: str
    created_at: datetime


class LineageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    evaluation_run_id: UUID
    artifact_ids: dict[str, str]
    checksum: str
    created_at: datetime
