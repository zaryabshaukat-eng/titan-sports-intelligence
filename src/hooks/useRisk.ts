import { queryOptions, useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/api/query-keys";
import { riskApi } from "@/api/risk";
import type { ResourceId } from "@/types/api";

export const riskAnalyzersQueryOptions = () =>
  queryOptions({ queryKey: queryKeys.riskAnalyzers, queryFn: () => riskApi.listAnalyzers() });
export const riskOutputsQueryOptions = (runId: ResourceId) =>
  queryOptions({
    queryKey: queryKeys.riskOutputs(runId),
    queryFn: () => riskApi.listOutputs(runId),
  });

export const useRiskAnalyzers = () => useQuery(riskAnalyzersQueryOptions());
export const useRiskOutputs = (runId?: ResourceId) =>
  useQuery({ ...riskOutputsQueryOptions(runId ?? ""), enabled: Boolean(runId) });
