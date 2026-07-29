import { queryOptions, useQuery } from "@tanstack/react-query";
import { marketsApi, type MarketQuery, type OddsQuery } from "@/api/markets";
import { queryKeys } from "@/api/query-keys";

export const marketsQueryOptions = (query: MarketQuery = {}) =>
  queryOptions({ queryKey: queryKeys.markets(query), queryFn: () => marketsApi.list(query) });

export const latestOddsQueryOptions = (query: OddsQuery = {}) =>
  queryOptions({
    queryKey: queryKeys.latestOdds(query),
    queryFn: () => marketsApi.listLatestOdds(query),
  });

export const useMarkets = (query: MarketQuery = {}) => useQuery(marketsQueryOptions(query));
export const useLatestOdds = (query: OddsQuery = {}) => useQuery(latestOddsQueryOptions(query));
