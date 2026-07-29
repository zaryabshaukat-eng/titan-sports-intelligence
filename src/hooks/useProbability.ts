import { queryOptions, useQuery } from "@tanstack/react-query";
import { probabilityApi } from "@/api/probability";
import { queryKeys } from "@/api/query-keys";
import type { PaginationParams, ResourceId } from "@/types/api";

export const probabilityModelsQueryOptions = () =>
  queryOptions({
    queryKey: queryKeys.probabilityModels,
    queryFn: () => probabilityApi.listModels(),
  });
export const probabilityRunsQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.probabilityRuns(query),
    queryFn: () => probabilityApi.listRuns(query),
  });
export const probabilityOutputsQueryOptions = (runId: ResourceId) =>
  queryOptions({
    queryKey: queryKeys.probabilityOutputs(runId),
    queryFn: () => probabilityApi.listOutputs(runId),
  });

export const useProbabilityModels = () => useQuery(probabilityModelsQueryOptions());
export const useProbabilityRuns = (query: PaginationParams = {}) =>
  useQuery(probabilityRunsQueryOptions(query));
export const useProbabilityOutputs = (runId?: ResourceId) =>
  useQuery({ ...probabilityOutputsQueryOptions(runId ?? ""), enabled: Boolean(runId) });
