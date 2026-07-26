"""Immutable Risk Engine assessments and reproducibility evidence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.risk.enums import RiskRunStatus, RiskValidationStatus
from app.shared.persistence.base import Base


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RiskRun(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "risk_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_risk_run_code"),
        UniqueConstraint("idempotency_key", name="uq_risk_run_idempotency"),
        Index("ix_risk_runs_consensus_created", "consensus_run_id", "created_at"),
    )
    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    consensus_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RiskRunStatus] = mapped_column(
        SqlEnum(RiskRunStatus, name="risk_run_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class RiskOutput(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "risk_outputs"
    __table_args__ = (
        UniqueConstraint(
            "risk_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_risk_output_run_fixture_market_outcome",
        ),
        CheckConstraint(
            "overall_risk_score >= 0 AND overall_risk_score <= 1",
            name="ck_risk_output_overall_range",
        ),
        Index("ix_risk_outputs_fixture_market", "fixture_id", "market_type", "outcome"),
    )
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fixture_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_type: Mapped[str] = mapped_column(String(96), nullable=False)
    outcome: Mapped[str] = mapped_column(String(96), nullable=False)
    overall_risk_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    uncertainty_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    stability_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    calibration_risk: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    agreement_risk: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    data_quality_risk: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    completeness_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    components: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)


class RiskLineage(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "risk_lineage"
    __table_args__ = (UniqueConstraint("risk_run_id", name="uq_risk_lineage_run"),)
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("risk_runs.id", ondelete="RESTRICT"), nullable=False
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("consensus_runs.id", ondelete="RESTRICT"), nullable=False
    )
    probability_run_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    dataset_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)


class RiskValidationRecord(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "risk_validation_records"
    __table_args__ = (
        UniqueConstraint("risk_run_id", "rule_name", name="uq_risk_validation_run_rule"),
        Index("ix_risk_validation_run", "risk_run_id"),
    )
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("risk_runs.id", ondelete="RESTRICT"), nullable=False
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[RiskValidationStatus] = mapped_column(
        SqlEnum(RiskValidationStatus, name="risk_validation_status"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
