import { queryOptions, useQuery } from "@tanstack/react-query";
import { matchesApi, type MatchQuery } from "@/api/matches";
import { queryKeys } from "@/api/query-keys";

export const matchesQueryOptions = (query: MatchQuery = {}) =>
  queryOptions({ queryKey: queryKeys.matches(query), queryFn: () => matchesApi.list(query) });

export const useMatches = (query: MatchQuery = {}) => useQuery(matchesQueryOptions(query));
