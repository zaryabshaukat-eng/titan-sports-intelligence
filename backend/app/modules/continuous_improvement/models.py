from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.continuous_improvement.enums import (
    DecisionStatus,
    ImprovementStatus,
    RecommendationType,
)
from app.shared.persistence.base import Base


class IdCreated:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ImprovementConfiguration(IdCreated, Base):
    __tablename__ = "improvement_configurations"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_improvement_config"),)
    code: Mapped[str] = mapped_column(String(96))
    version: Mapped[str] = mapped_column(String(64))
    analyzer_versions: Mapped[dict[str, str]] = mapped_column(JSONB)
    thresholds: Mapped[dict[str, object]] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64), unique=True)


class ImprovementRun(IdCreated, Base):
    __tablename__ = "improvement_runs"
    __table_args__ = (
        UniqueConstraint("run_code", name="uq_improvement_run"),
        UniqueConstraint("idempotency_key", name="uq_improvement_key"),
    )
    run_code: Mapped[str] = mapped_column(String(96))
    configuration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("improvement_configurations.id", ondelete="RESTRICT")
    )
    evaluation_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"),
        index=True,
    )
    backtest_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("backtest_runs.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[ImprovementStatus] = mapped_column(
        SqlEnum(ImprovementStatus, name="improvement_status")
    )
    input_checksum: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(64))


class Artifact(IdCreated, Base):
    __abstract__ = True
    improvement_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("improvement_runs.id", ondelete="RESTRICT"), index=True
    )


class Recommendation(Artifact):
    __tablename__ = "improvement_recommendations"
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        SqlEnum(RecommendationType, name="improvement_recommendation_type")
    )
    title: Mapped[str] = mapped_column(String(160))
    rationale: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column()
    analyzer_id: Mapped[str] = mapped_column(String(96))
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)


class RecommendationEvidence(Artifact):
    __tablename__ = "improvement_recommendation_evidence"
    recommendation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("improvement_recommendations.id", ondelete="RESTRICT")
    )
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB)


class CandidateModel(Artifact):
    __tablename__ = "improvement_candidate_models"
    model_identifier: Mapped[str] = mapped_column(String(96))
    model_version: Mapped[str] = mapped_column(String(64))
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB)


class CandidateFeature(Artifact):
    __tablename__ = "improvement_candidate_features"
    feature_set_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
    )
    action: Mapped[str] = mapped_column(String(64))
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB)


class PromotionDecision(Artifact):
    __tablename__ = "improvement_promotion_decisions"
    recommendation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("improvement_recommendations.id", ondelete="RESTRICT")
    )
    status: Mapped[DecisionStatus] = mapped_column(
        SqlEnum(DecisionStatus, name="improvement_decision_status")
    )
    note: Mapped[str] = mapped_column(Text)


class ValidationRecord(Artifact):
    __tablename__ = "improvement_validation_records"
    rule_name: Mapped[str] = mapped_column(String(96))
    status: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)


class LineageRecord(Artifact):
    __tablename__ = "improvement_lineage_records"
    artifact_ids: Mapped[dict[str, str]] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64))
