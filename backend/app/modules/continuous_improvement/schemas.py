from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.continuous_improvement.enums import ImprovementStatus


class RunCreate(BaseModel):
    run_code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    evaluation_run_id: UUID
    backtest_run_id: UUID
    configuration_code: str = Field(default="default", min_length=1, max_length=96)
    configuration_version: str = Field(default="1", min_length=1, max_length=64)
    thresholds: dict[str, float] = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    run_code: str
    evaluation_run_id: UUID
    backtest_run_id: UUID
    status: ImprovementStatus
    input_checksum: str
    created_at: datetime
