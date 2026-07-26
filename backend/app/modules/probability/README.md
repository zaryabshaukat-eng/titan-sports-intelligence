# Probability Engine

The Probability Engine produces reproducible, calibrated probability estimates from immutable Research dataset snapshots. It is an analytical computation boundary only: it does not generate betting recommendations, stakes, bankroll policies, arbitrage signals, or publication decisions.

## Run lifecycle

1. A caller selects an immutable Research dataset snapshot, matching Feature Set version, and matching Research experiment.
2. The service resolves an explicit model identifier/version from the registry and optional immutable calibration version.
3. It projects numeric `DatasetSnapshotRow` values into stable per-fixture feature vectors. No provider payload, live odds, or live Feature Store query is used.
4. Compatibility checks are persisted for feature-set/research lineage, fixture vectors, required features, model parameters, and calibration compatibility.
5. A valid run appends one `ProbabilityOutput` per fixture. An invalid run is retained as `validation_failed` with lineage and validation evidence but no outputs.
6. Evaluation accepts explicit settled binary observations for outputs from one run and appends immutable metric/reliability evidence.

Exact retries reuse their existing calibration, run, or evaluation through an idempotency fingerprint. A reused logical code with changed inputs is rejected, so a historical estimate can never be silently replaced.

## Models and inference

`ProbabilityModelRegistry` isolates business logic from model implementations. Initial reviewed baselines are:

- `logistic_baseline:1.0.0`: weighted logistic transform with explicit feature weights;
- `poisson_baseline:1.0.0`: event-occurrence probability from an explicit rate feature;
- `elo_baseline:1.0.0`: logistic conversion of canonical home/away rating features; and
- `bayesian_baseline:1.0.0`: beta-prior baseline with optional evidence feature.

Each model declares its metadata and required feature IDs. Future scikit-learn, PyTorch, or statistical adapters implement the same protocol and register a new explicit version; they do not alter the service or API flow. The initial baselines are deliberately transparent and are not trained production models.

## Calibration and ensembles

`CalibrationVersion` stores a code, version, method, parameters, owner, and optional compatible-model allowlist. The deterministic calibration registry supports Platt scaling, monotonic isotonic interpolation, and temperature scaling. Output intervals are calibrated using the same versioned monotonic transform as the estimate.

`ensemble.py` provides a pure positive-weighted average over uniquely named model estimates. It intentionally does not learn or optimize weights. A future ensemble model can persist its reviewed fixed weight configuration as a new model version without changing run lineage.

## Evaluation and lineage

`ProbabilityEvaluation` stores Brier score, log loss, calibration error, ROC AUC, PR AUC, sharpness, and reliability buckets. It records the exact output/observed-outcome input checksum, not an implicit live result query.

`ProbabilityLineage` includes the dataset snapshot, Feature Set version, Research experiment, model identifier/version, calibration version, parameter checksum, and random seed. PostgreSQL triggers reject updates and deletes for every Probability table, making the entire audit trail append-only.

## APIs and access control

All endpoints are versioned under `/api/v1/probability`.

- `POST /calibrations`, `POST /runs`, and `POST /runs/{id}/evaluations` require `probability:execute`.
- `GET /models`, calibration listings, run listings, outputs, evaluations, lineage, and validation evidence require `data:read`.

Collection endpoints use bounded pagination. Responses expose probability evidence only, never source-provider payloads or any recommendation policy.
