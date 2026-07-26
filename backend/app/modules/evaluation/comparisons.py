"""Read-only comparison of immutable evaluation metric artifacts."""

from __future__ import annotations

from typing import cast
from uuid import UUID


def compare(
    baseline_id: UUID, candidate_id: UUID, baseline: dict[str, object], candidate: dict[str, object]
) -> dict[str, object]:
    """Return candidate-minus-baseline deltas for shared numeric metrics.

    Metric direction is deliberately not interpreted here: the platform reports
    evidence, while future governance or policy layers decide what is acceptable.
    """
    deltas = {
        name: float(cast(int | float, candidate[name])) - float(cast(int | float, baseline[name]))
        for name in sorted(set(baseline).intersection(candidate))
        if isinstance(baseline[name], (int, float))
        and not isinstance(baseline[name], bool)
        and isinstance(candidate[name], (int, float))
        and not isinstance(candidate[name], bool)
    }
    return {
        "baseline_backtest_run_id": baseline_id,
        "candidate_backtest_run_id": candidate_id,
        "metric_deltas": deltas,
    }
