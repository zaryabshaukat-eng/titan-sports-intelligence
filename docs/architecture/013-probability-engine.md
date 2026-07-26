# 013 — Probability Engine

## Purpose

The Probability Engine is TITAN OS's first computational intelligence bounded context. It turns frozen Research dataset snapshots into calibrated, auditable estimates. It is intentionally not a recommendation, staking, or market-execution system.

## Dependency direction

```text
Canonical data → Feature Store version → Research dataset snapshot
                                           │
                              Research experiment + model version
                                           │
                              calibration version (optional)
                                           ▼
                                Probability Run (immutable)
                                           │
                         outputs / validation / lineage / evaluation
```

The engine reads only Research's immutable `DatasetSnapshot`, `DatasetSnapshotRow`, and `ResearchExperiment` artifacts. It does not query raw provider payloads, live Feature Store values, live market data, or direct Sports data during inference. This makes the estimate reproducible even after upstream sources evolve.

## Model abstraction

`ProbabilityModelRegistry` resolves explicit model identifier/version pairs. Initial logistic, Poisson, Elo, and beta-prior baselines use transparent deterministic formulas and declared feature requirements. The registry protocol is the extension point for later trained adapters; the service, persistence, validation, and API contracts are unchanged when a new reviewed model version is registered.

## Calibration, output, and ensemble policy

Calibration configurations are immutable named versions supporting Platt, isotonic, and temperature methods. A calibration may restrict compatible model identifiers. Each output retains the selected calibration version and a calibrated confidence interval.

The ensemble helper accepts explicit positive weights and combines supplied model outputs deterministically. Weight learning is deliberately outside this phase. Any future ensemble must be a versioned model/configuration with the same lineage obligations.

## Validation, lineage, and evaluation

Before outputs are written, the engine validates:

- Feature Set version agreement across the request, dataset, and experiment;
- research experiment-to-dataset compatibility;
- presence of numeric fixture-scoped vectors;
- declared model feature and parameter compatibility; and
- optional calibration compatibility.

Failed validations create immutable `validation_failed` runs, validation records, and lineage but no estimates. Completed runs write one immutable output per fixture. Evaluation is also append-only and calculates Brier score, log loss, calibration error, ROC AUC, PR AUC, sharpness, and reliability from explicit output/outcome pairs.

Every Probability record is protected by PostgreSQL update/delete-rejection triggers. The lineage record carries the dataset, Feature Set version, Research experiment, model version, calibration version, parameter checksum, and random seed required for replay.

## Security and scope

Execution operations require `probability:execute`; read-only evidence requires `data:read`. This boundary contains no recommendation, stake sizing, bankroll management, arbitrage, or frontend behavior.
