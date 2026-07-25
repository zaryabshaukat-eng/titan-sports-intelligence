"""Provider-neutral validation and read contracts for immutable statistics."""

# ruff: noqa: E501, E701, E702
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.statistics.enums import StatisticScope


class FixtureReference(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    id: str = Field(min_length=1, max_length=128)


class SubjectReference(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=160)
    birth_date: str | None = None


class CategoryInput(BaseModel):
    code: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=160)
    value_schema: dict[str, object] = Field(default_factory=dict, validation_alias="schema")


class NormalizedStatistic(BaseModel):
    scope: StatisticScope
    category: CategoryInput
    values: dict[str, object] = Field(min_length=1)
    team: SubjectReference | None = None
    player: SubjectReference | None = None
    version: str = Field(default="1", max_length=64)


class NormalizedStatisticsPayload(BaseModel):
    fixture: FixtureReference
    observed_at: datetime
    statistics: list[NormalizedStatistic] = Field(min_length=1)

    @field_validator("observed_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must include timezone")
        return value


class StatisticsIngestionRequest(BaseModel):
    payloads: list[dict[str, object]] = Field(min_length=1, max_length=500)


class IngestionItemRead(BaseModel):
    source_index: int
    outcome: str
    snapshots_created: int = 0
    validation_errors: list[dict[str, object]] = Field(default_factory=list)


class StatisticsIngestionResult(BaseModel):
    run_id: UUID
    provider: str
    items: list[IngestionItemRead]


class Pagination(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    description: str | None
    value_schema: dict[str, object]
    is_active: bool


class SnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    fixture_id: UUID
    provider_id: UUID
    scope: StatisticScope
    series_id: UUID
    values: dict[str, object]
    observed_at: datetime
    checksum: str
