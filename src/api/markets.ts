import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { Market, OddsSnapshot } from "@/types/domain";

export interface MarketQuery extends PaginationParams {
  fixture_id?: ResourceId;
  market_type_id?: ResourceId;
  market_status_id?: ResourceId;
}

export interface OddsQuery extends PaginationParams {
  fixture_id?: ResourceId;
  market_id?: ResourceId;
  bookmaker_id?: ResourceId;
  selection_id?: ResourceId;
}

export const marketsApi = {
  async list(query: MarketQuery = {}, options?: RequestOptions): Promise<ApiPage<Market>> {
    return (await apiClient.get<ApiPage<Market>>("/market-data/markets", { ...options, query }))
      .data;
  },
  async get(marketId: ResourceId, options?: RequestOptions): Promise<Market> {
    return (await apiClient.get<Market>(`/market-data/markets/${marketId}`, options)).data;
  },
  async listLatestOdds(
    query: OddsQuery = {},
    options?: RequestOptions,
  ): Promise<ApiPage<OddsSnapshot>> {
    return (
      await apiClient.get<ApiPage<OddsSnapshot>>("/market-data/latest-odds", { ...options, query })
    ).data;
  },
};
