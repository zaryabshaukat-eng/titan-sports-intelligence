import { apiClient, type RequestOptions } from "./client";
import type { ResourceId } from "@/types/api";
import type { Explainer, Explanation } from "@/types/domain";

export const explainabilityApi = {
  async listEngines(options?: RequestOptions): Promise<Explainer[]> {
    return (await apiClient.get<Explainer[]>("/explainability/engines", options)).data;
  },
  async listExplanations(runId: ResourceId, options?: RequestOptions): Promise<Explanation[]> {
    return (
      await apiClient.get<Explanation[]>(`/explainability/runs/${runId}/explanations`, options)
    ).data;
  },
};
