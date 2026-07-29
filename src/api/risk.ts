import { apiClient, type RequestOptions } from "./client";
import type { ResourceId } from "@/types/api";
import type { RiskAnalyzer, RiskOutput } from "@/types/domain";

export const riskApi = {
  async listAnalyzers(options?: RequestOptions): Promise<RiskAnalyzer[]> {
    return (await apiClient.get<RiskAnalyzer[]>("/risk/analyzers", options)).data;
  },
  async listOutputs(runId: ResourceId, options?: RequestOptions): Promise<RiskOutput[]> {
    return (await apiClient.get<RiskOutput[]>(`/risk/runs/${runId}/outputs`, options)).data;
  },
};
