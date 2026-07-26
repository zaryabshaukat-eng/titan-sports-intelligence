from enum import StrEnum


class ImprovementStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class RecommendationType(StrEnum):
    FEATURE_RETIREMENT = "feature_retirement"
    FEATURE_PROMOTION = "feature_promotion"
    FEATURE_REDESIGN = "feature_redesign"
    MODEL_RETIREMENT = "model_retirement"
    MODEL_PROMOTION = "model_promotion"
    CALIBRATION_REPLACEMENT = "calibration_replacement"
    CONSENSUS_CHANGE = "consensus_change"
    RISK_ADJUSTMENT = "risk_adjustment"
    RESEARCH_PRIORITY = "research_priority"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
