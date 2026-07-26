# Research Engine

The Research Engine is TITAN's reproducible scientific experimentation boundary. It uses only immutable, canonical Feature Store values; it never reads raw provider payloads, live odds, or live statistics. It implements exploratory statistical analysis only—there are no prediction models, probability estimates, betting decisions, or recommendations in this module.

## Artifacts and lifecycle

1. A caller selects one explicit `FeatureSetVersion` and a bounded set of Feature Store feature IDs and canonical subject/time filters.
2. The service materializes the exact matching `FeatureValue` records into `DatasetSnapshot` and `DatasetSnapshotRow` records. The copied rows, selection, checksum, source count, and Feature Store generator version form a frozen dataset.
3. An experiment refers to that snapshot and the same Feature Set version. It records a name, owner, analysis parameters, random seed, input checksum, generator versions, validation findings, and lineage before persisting a result.
4. Analysts may register a stable hypothesis and append a reviewed hypothesis evaluation tied to an experiment and, optionally, one statistic result.

Every artifact is append-only. PostgreSQL triggers reject updates and deletes on research tables. Retrying an identical dataset or experiment request returns the existing artifact by idempotency key; using the same dataset version or experiment code with different inputs produces a conflict rather than silently changing history.

## Data model

- `DatasetSnapshot` is the named, versioned Feature Store projection and its complete selection/checksum.
- `DatasetSnapshotRow` copies the source value, Feature Definition, subject identifiers, timestamps, and numeric value needed to analyse that projection later.
- `ResearchExperiment` is a terminal record with `completed` or `validation_failed` status; it retains its Feature Set version, dataset, parameters, seed, generator versions, and checksum.
- `ExperimentStatisticResult` stores a descriptive, distribution, Pearson correlation, or documented exploratory Welch-style significance result.
- `ResearchHypothesis` and `HypothesisEvaluation` preserve the analyst's statement and human-reviewed conclusion/evidence without overwriting either.
- `ExperimentLineage` holds the experiment-to-dataset/version/generator/parameter/seed replay path.
- `ExperimentValidationRecord` stores version, feature selection, and numeric-observation checks, including failures.

## Statistical framework

The registry intentionally contains small deterministic functions:

- descriptive statistics with a normal-approximation confidence interval;
- equal-width distributions;
- Pearson correlation joined through a stable canonical subject key; and
- an explicitly documented exploratory Welch-style normal approximation.

The functions are pure Python and run only over `DatasetSnapshotRow` values. Adding a reviewed analysis means adding a registry implementation and its tests; it does not require changing the dataset model or provider adapters.

## API and authorization

All endpoints are versioned under `/api/v1/research`.

- `POST /datasets`, `POST /experiments`, `POST /hypotheses`, and `POST /hypotheses/evaluations` require `research:execute`.
- Dataset, row, experiment, result, lineage, validation, hypothesis, and evaluation reads require `data:read`.

Read endpoints are paginated where the collection can grow. The API exposes metadata and evidence but never provider payloads.

## Reproducing an experiment

Use the experiment's dataset snapshot, Feature Set version, generator-version map, parameters checksum, and random seed from the lineage endpoint. The referenced dataset rows are retained separately from mutable operational tables, so the same analysis can be recomputed without a live Feature Store query. A different feature version, source selection, or parameter set must be recorded as a new artifact.
