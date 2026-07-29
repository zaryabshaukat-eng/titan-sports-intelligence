import { queryOptions, useQuery } from "@tanstack/react-query";
import { evaluationApi } from "@/api/evaluation";
import { queryKeys } from "@/api/query-keys";
import type { PaginationParams, ResourceId } from "@/types/api";

export const evaluationScenariosQueryOptions = () =>
  queryOptions({
    queryKey: queryKeys.evaluationScenarios,
    queryFn: () => evaluationApi.listScenarios(),
  });
export const backtestsQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.backtests(query),
    queryFn: () => evaluationApi.listBacktests(query),
  });
export const backtestQueryOptions = (id: ResourceId) =>
  queryOptions({ queryKey: queryKeys.backtest(id), queryFn: () => evaluationApi.getBacktest(id) });

export const useEvaluationScenarios = () => useQuery(evaluationScenariosQueryOptions());
export const useBacktests = (query: PaginationParams = {}) =>
  useQuery(backtestsQueryOptions(query));
export const useBacktest = (id?: ResourceId) =>
  useQuery({ ...backtestQueryOptions(id ?? ""), enabled: Boolean(id) });
