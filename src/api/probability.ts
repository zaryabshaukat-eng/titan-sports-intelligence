import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { ProbabilityModel, ProbabilityOutput, ProbabilityRun } from "@/types/domain";

export const probabilityApi = {
  async listModels(options?: RequestOptions): Promise<ProbabilityModel[]> {
    return (await apiClient.get<ProbabilityModel[]>("/probability/models", options)).data;
  },
  async listRuns(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<ProbabilityRun>> {
    return (
      await apiClient.get<ApiPage<ProbabilityRun>>("/probability/runs", { ...options, query })
    ).data;
  },
  async listOutputs(runId: ResourceId, options?: RequestOptions): Promise<ProbabilityOutput[]> {
    return (await apiClient.get<ProbabilityOutput[]>(`/probability/runs/${runId}/outputs`, options))
      .data;
  },
};
