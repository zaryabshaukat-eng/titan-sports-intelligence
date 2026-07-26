# 011 — Research Engine

## Purpose

The Research Engine is TITAN OS's scientific experimentation layer. It enables analysts to make, compare, and reproduce statistical observations using only one explicit, immutable Feature Store version. It is deliberately separate from future probability, recommendation, evaluation, and machine-learning bounded contexts.

## Boundary and dependency direction

Research has one upstream data dependency: the canonical Feature Store. Dataset creation reads versioned `FeatureSetVersion`, `FeatureDefinition`, and `FeatureValue` records once, then persists a materialized local snapshot. Experiment execution reads only that local snapshot. It does not access provider payloads or call ingestion, market, statistics, or Sports repositories directly.

```text
Canonical Sports / Statistics / Market Data
                │
                ▼
          Feature Store (versioned)
                │ explicit version and selection
                ▼
       Research dataset snapshot (immutable)
                │
                ▼
  experiment + validation + lineage + results
                │
                ▼
     reviewed hypothesis evidence (optional)
```

This direction prevents live-data leakage and means downstream intelligence modules can cite a stable research artifact rather than a transient query.

## Reproducibility and immutability

Every dataset records its Feature Set version, selection, source-value checksum, generator versions, and copied observations. Every experiment records its dataset, Feature Set version, generator versions, parameters, random seed, checksum, validation output, and lineage. All research data tables are append-only through PostgreSQL update/delete-rejection triggers. Idempotency keys return an identical prior artifact on retry; a reused dataset version or experiment code with changed inputs is rejected.

## Analysis policy

The initial analysis registry offers descriptive statistics, distributions, Pearson correlation, and an exploratory Welch-style significance test. All methods are deterministic and dependency-light. They are research evidence, not forecasts, probabilities, ranking scores, or decisions. New analysis methods must be versioned/reviewed before registry registration and tested against frozen fixtures.

## Hypotheses

`ResearchHypothesis` stores the statement and owner separately from `HypothesisEvaluation`. Evaluations are appended and must be tied to a real experiment; an optional result reference is verified to belong to that experiment. The service verifies any supplied significance claim against its p-value and does not infer recommendations.

## APIs and access control

`research:execute` protects creation of datasets, experiments, hypotheses, and evaluations. `data:read` protects all read endpoints. API paths are under `/api/v1/research`, provide OpenAPI contracts, and use pagination for materialized datasets and catalog listings.

## Operational considerations

Dataset snapshot materialization is an offline/internal operation. Large selections should be partitioned by explicit time or canonical-subject filters and monitored through existing request, database, and correlation-ID telemetry. The initial statistical functions run in-process because they are intentionally small; long-running or high-cardinality analyses should later be scheduled through a dedicated worker without weakening the frozen-dataset contract.
