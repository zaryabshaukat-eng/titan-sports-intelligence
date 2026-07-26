"""Append-only Explainability runs, rendered explanations, and audit evidence."""

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

from app.modules.explainability.enums import ExplainabilityRunStatus, ExplainabilityValidationStatus
from app.shared.persistence.base import Base


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExplainabilityRun(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explainability_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_explainability_run_code"),
        UniqueConstraint("idempotency_key", name="uq_explainability_run_idempotency"),
        Index("ix_explainability_runs_risk_created", "risk_run_id", "created_at"),
    )
    run_code: Mapped[str] = mapped_column(String(96), nullable=False)
    probability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("probability_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("risk_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
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
    parameters: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    status: Mapped[ExplainabilityRunStatus] = mapped_column(
        SqlEnum(ExplainabilityRunStatus, name="explainability_run_status"), nullable=False
    )
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class Explanation(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explanations"
    __table_args__ = (
        UniqueConstraint(
            "explainability_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_explanation_run_fixture_market_outcome",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_explanation_confidence_range"
        ),
        Index("ix_explanations_fixture_market", "fixture_id", "market_type", "outcome"),
    )
    explainability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explainability_runs.id", ondelete="RESTRICT"),
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
    explanation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    evidence_completeness: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    traceability_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    coverage_score: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)


class FeatureContribution(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explanation_feature_contributions"
    __table_args__ = (
        UniqueConstraint(
            "explanation_id", "feature_id", name="uq_explanation_contribution_feature"
        ),
    )
    explanation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explanations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_id: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    contribution: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    source_feature_value_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feature_store_feature_values.id", ondelete="RESTRICT"),
        nullable=False,
    )


class EvidenceReference(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explanation_evidence_references"
    __table_args__ = (
        UniqueConstraint("explanation_id", "sequence", name="uq_explanation_evidence_sequence"),
    )
    explanation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explanations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class ReasoningStep(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explanation_reasoning_steps"
    __table_args__ = (
        UniqueConstraint("explanation_id", "position", name="uq_explanation_reasoning_position"),
    )
    explanation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explanations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)


class ExplainabilityLineage(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explainability_lineage"
    __table_args__ = (
        UniqueConstraint("explainability_run_id", name="uq_explainability_lineage_run"),
    )
    explainability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explainability_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    probability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("probability_runs.id", ondelete="RESTRICT"), nullable=False
    )
    consensus_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("consensus_runs.id", ondelete="RESTRICT"), nullable=False
    )
    risk_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("risk_runs.id", ondelete="RESTRICT"), nullable=False
    )
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
    research_experiment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parameters_checksum: Mapped[str] = mapped_column(String(64), nullable=False)


class ExplainabilityValidationRecord(UUIDMixin, CreatedMixin, Base):
    __tablename__ = "explainability_validation_records"
    __table_args__ = (
        UniqueConstraint(
            "explainability_run_id", "rule_name", name="uq_explainability_validation_run_rule"
        ),
        Index("ix_explainability_validation_run", "explainability_run_id"),
    )
    explainability_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("explainability_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[ExplainabilityValidationStatus] = mapped_column(
        SqlEnum(ExplainabilityValidationStatus, name="explainability_validation_status"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
