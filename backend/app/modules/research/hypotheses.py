"""Hypothesis evaluation policy helpers; conclusions remain human-reviewed research artifacts."""

from __future__ import annotations

from decimal import Decimal

from app.modules.research.enums import HypothesisDecision


def significance_from_p_value(
    p_value: Decimal | None, *, alpha: Decimal = Decimal("0.05")
) -> bool | None:
    """Return significance without treating it as a recommendation or prediction."""
    return p_value <= alpha if p_value is not None else None


def validate_decision(decision: HypothesisDecision, significant: bool | None) -> bool:
    """Reject an unsupported conclusion when no statistical evidence was supplied."""
    if decision is HypothesisDecision.SUPPORTED:
        return significant is True
    if decision is HypothesisDecision.REJECTED:
        return significant is True
    return True
