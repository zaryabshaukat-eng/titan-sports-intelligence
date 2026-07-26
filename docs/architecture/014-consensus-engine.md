# 014 — Consensus Engine

Consensus is an append-only evidence-combination boundary between Probability and later risk/governance modules. It reads only immutable Probability runs, outputs, and evaluation artifacts, validates common Feature Set and dataset lineage, and writes a new immutable consensus run.

Each output is a fixture/market/outcome group. Registered weighted-average, median, trimmed-mean, majority-vote, and beta-prior strategies combine explicit inputs. The result stores confidence (agreement, calibration-quality evidence, completeness), disagreement (standard deviation, spread, pairwise divergence, entropy), contributor counts, and agreement level. No strategy compares sportsbook odds or makes a recommendation.

Lineage retains probability-run IDs, model versions, calibration versions, research experiment IDs, dataset/version references, parameter checksum, and seed. PostgreSQL triggers prevent mutation. Future governance or risk modules can judge whether the evidence is publishable without changing Consensus computation.
