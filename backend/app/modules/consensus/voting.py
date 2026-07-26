"""Majority-voting helper independent from recommendation policy."""

from app.modules.consensus.engines import ConsensusEstimate, MajorityVoting


def majority_vote(estimates: list[ConsensusEstimate], threshold: float = 0.5) -> float:
    return MajorityVoting().combine(estimates, {"threshold": threshold})
