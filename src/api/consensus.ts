import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { ConsensusOutput, ConsensusRun, ConsensusStrategy } from "@/types/domain";

export const consensusApi = {
  async listStrategies(options?: RequestOptions): Promise<ConsensusStrategy[]> {
    return (await apiClient.get<ConsensusStrategy[]>("/consensus/strategies", options)).data;
  },
  async listRuns(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<ConsensusRun>> {
    return (await apiClient.get<ApiPage<ConsensusRun>>("/consensus/runs", { ...options, query }))
      .data;
  },
  async listOutputs(runId: ResourceId, options?: RequestOptions): Promise<ConsensusOutput[]> {
    return (await apiClient.get<ConsensusOutput[]>(`/consensus/runs/${runId}/outputs`, options))
      .data;
  },
};
