from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.evaluation.backtest import no_future_leakage
from app.modules.evaluation.comparisons import compare
from app.modules.evaluation.enums import ScenarioType
from app.modules.evaluation.metrics import calculate
from app.modules.evaluation.registry import ScenarioRegistry
from app.modules.evaluation.schemas import BacktestRunCreate, HistoricalOutcome
from app.modules.evaluation.validation import validate_scenario_parameters


def test_historical_scenarios_metrics_and_leakage_are_deterministic() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    items = [SimpleNamespace(fixture_start_at=now + timedelta(days=index)) for index in range(5)]
    assert (
        ScenarioRegistry().resolve("rolling_window").select(items, {"window_size": 2}) == items[-2:]
    )
    assert no_future_leakage(now, now) and not no_future_leakage(now + timedelta(seconds=1), now)
    metrics, reliability = calculate(
        [
            SimpleNamespace(predicted_probability=Decimal("0.8"), observed_outcome=True),
            SimpleNamespace(predicted_probability=Decimal("0.2"), observed_outcome=False),
        ]
    )
    assert metrics["brier_score"] < 0.1 and sum(item["count"] for item in reliability) == 2
    assert metrics["accuracy"] == 1.0
    assert metrics["coverage"] == 1.0
    assert metrics["prediction_stability"] > 0.0


def test_replay_input_rejects_duplicates_and_invalid_scenario_parameters() -> None:
    output_id = uuid4()
    with pytest.raises(ValueError, match="only once"):
        BacktestRunCreate(
            run_code="duplicate_output",
            research_experiment_id=uuid4(),
            probability_run_id=uuid4(),
            consensus_run_id=uuid4(),
            risk_run_id=uuid4(),
            explainability_run_id=uuid4(),
            scenario=ScenarioType.HISTORICAL_REPLAY,
            random_seed=1,
            outcomes=[
                HistoricalOutcome(probability_output_id=output_id, observed_outcome=True),
                HistoricalOutcome(probability_output_id=output_id, observed_outcome=False),
            ],
        )
    with pytest.raises(ValueError, match="window_size"):
        validate_scenario_parameters(ScenarioType.ROLLING_WINDOW, {"window_size": 0})
    with pytest.raises(ValueError, match="test_fraction"):
        validate_scenario_parameters(ScenarioType.TIME_SPLIT, {"test_fraction": 0})


def test_comparisons_are_numeric_evidence_only() -> None:
    baseline = uuid4()
    candidate = uuid4()
    value = compare(
        baseline,
        candidate,
        {"brier_score": 0.2, "roc_auc": None, "label": "baseline"},
        {"brier_score": 0.1, "roc_auc": 0.8, "label": "candidate"},
    )
    assert value["baseline_backtest_run_id"] == baseline
    assert value["candidate_backtest_run_id"] == candidate
    assert value["metric_deltas"] == {"brier_score": -0.1}
