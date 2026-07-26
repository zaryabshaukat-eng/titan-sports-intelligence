# 017 - Backtesting & Simulation

The Evaluation bounded context performs deterministic chronological replay of frozen pipeline artifacts. Backtest runs retain all upstream artifact identities and scenario configuration. Replay rejects outputs whose prediction timestamp is after the canonical fixture kickoff, preventing future leakage.

Scenario implementations are registry-driven. Historical replay, rolling window, expanding window, walk-forward, and time split are selection policies over ordered historical observations; no production recommendation policy exists here. Metrics and reliability are persisted as immutable audit evidence. Read-only comparisons report metric deltas between backtests, while any future decision policy remains outside this bounded context.
