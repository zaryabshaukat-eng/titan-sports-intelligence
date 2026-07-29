import { queryOptions, useQuery } from "@tanstack/react-query";
import { explainabilityApi } from "@/api/explainability";
import { queryKeys } from "@/api/query-keys";
import type { ResourceId } from "@/types/api";

export const explainersQueryOptions = () =>
  queryOptions({ queryKey: queryKeys.explainers, queryFn: () => explainabilityApi.listEngines() });
export const explanationsQueryOptions = (runId: ResourceId) =>
  queryOptions({
    queryKey: queryKeys.explanations(runId),
    queryFn: () => explainabilityApi.listExplanations(runId),
  });

export const useExplainers = () => useQuery(explainersQueryOptions());
export const useExplanations = (runId?: ResourceId) =>
  useQuery({ ...explanationsQueryOptions(runId ?? ""), enabled: Boolean(runId) });
