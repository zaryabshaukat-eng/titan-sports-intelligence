# Consensus Engine

The Consensus Engine combines only compatible immutable `ProbabilityRun` outputs. It produces an evidence-backed consensus probability, confidence metrics, and disagreement metrics; it contains no odds comparison, expected value, recommendation, stake, bankroll, or arbitrage behavior.

Each run validates that every input Probability run completed against one Research dataset and Feature Set version. It records every run/model/calibration/research-experiment input, the strategy, parameters, seed, validation results, and lineage. Invalid combinations persist a `validation_failed` audit artifact without outputs.

The pluggable registry provides weighted average, median, trimmed mean, majority voting, and beta-prior pooling. Weights are explicit and fixed; the engine never optimizes them automatically. Outputs are grouped by canonical fixture, market type, and outcome and retain contributor completeness, standard deviation, spread, pairwise divergence, entropy, confidence components, and agreement level.

Confidence is evidence-only: model agreement, available Probability evaluation calibration quality, and input completeness are averaged. It is not a publication or recommendation decision. All tables are append-only via PostgreSQL triggers. APIs are under `/api/v1/consensus`; writes require `consensus:execute` and evidence reads require `data:read`.
