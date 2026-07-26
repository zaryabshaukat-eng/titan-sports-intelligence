# Risk Engine

The Risk Engine produces immutable reliability and uncertainty assessments from Consensus evidence. It does not access bookmaker odds, calculate expected value, recommend actions, or manage stakes.

Each Risk run validates a completed Consensus run, its output evidence, and lineage. It then applies registry-selected analyzers independently for entropy/spread uncertainty, stability, calibration risk, agreement risk, and contributor completeness/data-quality risk. The overall score is a transparent average of these components, retained alongside each component value.

Risk lineage preserves the Consensus run, Probability run IDs, Feature Set and dataset versions, parameter checksum, and seed. All Risk tables are append-only through PostgreSQL triggers. APIs are under `/api/v1/risk`; writes require `risk:execute` and reads require `data:read`.
