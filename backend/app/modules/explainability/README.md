# Explainability Engine

Explainability creates immutable evidence packages for compatible Probability, Consensus, and Risk outputs. It is descriptive only: no wagering, odds comparison, expected value, staking, or policy justification is produced.

Each run verifies a common frozen Research dataset and Feature Set version, then creates per-fixture explanations. Feature contributions are deterministic normalized shares of immutable numeric dataset rows. Evidence references point to dataset, feature values, Probability output, Consensus output, and Risk assessment. The reasoning chain preserves their ordered relationship.

Every explanation also stores confidence, evidence completeness, traceability, coverage, run lineage, and validation evidence. The registry exposes a provider-neutral deterministic explainer; future SHAP or integrated-gradient adapters can implement the same interface. APIs are versioned under `/api/v1/explainability`; writes require `explainability:execute`, reads require `data:read`.
