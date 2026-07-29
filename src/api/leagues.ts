import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { League } from "@/types/domain";

export interface LeagueQuery extends PaginationParams {
  q?: string;
  country_id?: ResourceId;
  sport?: string;
}

export const leaguesApi = {
  async list(query: LeagueQuery = {}, options?: RequestOptions): Promise<ApiPage<League>> {
    return (await apiClient.get<ApiPage<League>>("/sports/leagues", { ...options, query })).data;
  },
  async get(leagueId: ResourceId, options?: RequestOptions): Promise<League> {
    return (await apiClient.get<League>(`/sports/leagues/${leagueId}`, options)).data;
  },
};
