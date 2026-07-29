import { queryOptions, useQuery } from "@tanstack/react-query";
import { consensusApi } from "@/api/consensus";
import { queryKeys } from "@/api/query-keys";
import type { PaginationParams, ResourceId } from "@/types/api";

export const consensusStrategiesQueryOptions = () =>
  queryOptions({
    queryKey: queryKeys.consensusStrategies,
    queryFn: () => consensusApi.listStrategies(),
  });
export const consensusRunsQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.consensusRuns(query),
    queryFn: () => consensusApi.listRuns(query),
  });
export const consensusOutputsQueryOptions = (runId: ResourceId) =>
  queryOptions({
    queryKey: queryKeys.consensusOutputs(runId),
    queryFn: () => consensusApi.listOutputs(runId),
  });

export const useConsensusStrategies = () => useQuery(consensusStrategiesQueryOptions());
export const useConsensusRuns = (query: PaginationParams = {}) =>
  useQuery(consensusRunsQueryOptions(query));
export const useConsensusOutputs = (runId?: ResourceId) =>
  useQuery({ ...consensusOutputsQueryOptions(runId ?? ""), enabled: Boolean(runId) });
