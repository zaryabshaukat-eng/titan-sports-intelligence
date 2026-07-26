# Continuous Evaluation Platform

This bounded context continuously measures the health of immutable TITAN analytical artifacts. A monitoring run starts from an immutable Backtest run and preserves its Feature Store, Research dataset, Probability, Consensus, Risk, Explainability, model, calibration, and version lineage.

It evaluates evidence only: it never reads provider payloads, creates predictions, changes source artifacts, or makes recommendations. Registry-driven PSI, KL divergence, Jensen-Shannon divergence, and Wasserstein analyzers persist reproducible drift measurements. Provider freshness and completeness are supplied as canonical operational observations and are stored as append-only health history.

All tables use PostgreSQL mutation-rejection triggers. The public API requires `evaluation-monitoring:execute` to create a run and `data:read` to view its evidence.
