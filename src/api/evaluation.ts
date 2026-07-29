import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { BacktestRun, EvaluationScenario } from "@/types/domain";

export const evaluationApi = {
  async listScenarios(options?: RequestOptions): Promise<EvaluationScenario[]> {
    return (await apiClient.get<EvaluationScenario[]>("/evaluation/scenarios", options)).data;
  },
  async listBacktests(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<BacktestRun>> {
    return (
      await apiClient.get<ApiPage<BacktestRun>>("/evaluation/backtests", { ...options, query })
    ).data;
  },
  async getBacktest(backtestId: ResourceId, options?: RequestOptions): Promise<BacktestRun> {
    return (await apiClient.get<BacktestRun>(`/evaluation/backtests/${backtestId}`, options)).data;
  },
};
