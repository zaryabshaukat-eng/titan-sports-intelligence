import type { LeagueQuery } from "./leagues";
import type { MarketQuery, OddsQuery } from "./markets";
import type { MatchQuery } from "./matches";
import type { PaginationParams, ResourceId } from "@/types/api";

/** Stable query keys shared by hooks and future cache invalidation. */
export const queryKeys = {
  dashboard: ["dashboard"] as const,
  matches: (query: MatchQuery) => ["matches", query] as const,
  leagues: (query: LeagueQuery) => ["leagues", query] as const,
  markets: (query: MarketQuery) => ["markets", query] as const,
  latestOdds: (query: OddsQuery) => ["markets", "latest-odds", query] as const,
  datasets: (query: PaginationParams) => ["research", "datasets", query] as const,
  experiments: (query: PaginationParams) => ["research", "experiments", query] as const,
  hypotheses: (query: PaginationParams) => ["research", "hypotheses", query] as const,
  probabilityModels: ["probability", "models"] as const,
  probabilityRuns: (query: PaginationParams) => ["probability", "runs", query] as const,
  probabilityOutputs: (runId: ResourceId) => ["probability", "outputs", runId] as const,
  consensusStrategies: ["consensus", "strategies"] as const,
  consensusRuns: (query: PaginationParams) => ["consensus", "runs", query] as const,
  consensusOutputs: (runId: ResourceId) => ["consensus", "outputs", runId] as const,
  riskAnalyzers: ["risk", "analyzers"] as const,
  riskOutputs: (runId: ResourceId) => ["risk", "outputs", runId] as const,
  explainers: ["explainability", "engines"] as const,
  explanations: (runId: ResourceId) => ["explainability", "explanations", runId] as const,
  evaluationScenarios: ["evaluation", "scenarios"] as const,
  backtests: (query: PaginationParams) => ["evaluation", "backtests", query] as const,
  backtest: (id: ResourceId) => ["evaluation", "backtest", id] as const,
};
