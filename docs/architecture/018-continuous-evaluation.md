# 018 - Continuous Evaluation Platform

Continuous Evaluation is a separate bounded context that consumes only immutable pipeline artifacts. It begins from a Backtest run, validates the referenced lineage, and stores append-only quality, drift, provider, model, feature, calibration, alert, validation, and lineage evidence.

Analyzer registration is the extension boundary. New deterministic analyzers can be added without changing orchestration. Baseline selection currently uses the most recent completed monitoring run; production scheduling and notification policy remain outside this context.
