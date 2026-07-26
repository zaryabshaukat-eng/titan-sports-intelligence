# 016 — Explainability Engine

Explainability is an append-only evidence layer joining frozen Feature Store/Research rows to Probability, Consensus, and Risk output artifacts. It validates common dataset/version lineage before generating a fixture explanation, feature contribution records, evidence references, and an ordered reasoning chain.

Initial contributions are deterministic normalized numeric-feature shares. The contribution registry is the extension point for future model-specific explainers without changing persistence, lineage, or API contracts. Each explanation retains confidence, evidence completeness, traceability, and coverage—not any recommendation or decision policy.
