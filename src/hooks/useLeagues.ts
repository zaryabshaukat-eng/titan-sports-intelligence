import { queryOptions, useQuery } from "@tanstack/react-query";
import { leaguesApi, type LeagueQuery } from "@/api/leagues";
import { queryKeys } from "@/api/query-keys";

export const leaguesQueryOptions = (query: LeagueQuery = {}) =>
  queryOptions({ queryKey: queryKeys.leagues(query), queryFn: () => leaguesApi.list(query) });

export const useLeagues = (query: LeagueQuery = {}) => useQuery(leaguesQueryOptions(query));
