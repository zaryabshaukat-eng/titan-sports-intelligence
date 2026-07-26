# Backtesting & Simulation Platform

Evaluation replays only immutable historical Probability outputs against explicitly supplied historical outcomes. Before a result is persisted, each prediction timestamp must be at or before the canonical fixture kickoff timestamp; a violation creates a validation-failed backtest rather than using future information.

The scenario registry provides historical replay, rolling window, expanding window, walk-forward, and time-split selection interfaces. Replay is chronologically ordered and deterministic. Metrics include accuracy, Brier score, log loss, calibration error, ROC-AUC, PR-AUC, sharpness, coverage, prediction stability, and reliability through the shared probability metric implementation.

Every Backtest run preserves Feature Store/Research/Probability/Consensus/Risk/Explainability identities, Probability model and calibration versions, scenario parameters, seed, results, metrics, validation evidence, and lineage. Read-only comparison returns numeric metric deltas between immutable runs; it does not determine policy or select a winner. The module contains no odds comparison, recommendation, expected value, bankroll, stake, or arbitrage policy.
