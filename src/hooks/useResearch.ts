import { queryOptions, useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/api/query-keys";
import { researchApi } from "@/api/research";
import type { PaginationParams } from "@/types/api";

export const datasetsQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.datasets(query),
    queryFn: () => researchApi.listDatasets(query),
  });
export const experimentsQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.experiments(query),
    queryFn: () => researchApi.listExperiments(query),
  });
export const hypothesesQueryOptions = (query: PaginationParams = {}) =>
  queryOptions({
    queryKey: queryKeys.hypotheses(query),
    queryFn: () => researchApi.listHypotheses(query),
  });

export const useDatasets = (query: PaginationParams = {}) => useQuery(datasetsQueryOptions(query));
export const useExperiments = (query: PaginationParams = {}) =>
  useQuery(experimentsQueryOptions(query));
export const useHypotheses = (query: PaginationParams = {}) =>
  useQuery(hypothesesQueryOptions(query));
