import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams, ResourceId } from "@/types/api";
import type { Match } from "@/types/domain";

export interface MatchQuery extends PaginationParams {
  season_id?: ResourceId;
  competition_id?: ResourceId;
  home_team_id?: ResourceId;
  away_team_id?: ResourceId;
  venue_id?: ResourceId;
  fixture_status_id?: ResourceId;
  fixture_status_code?: string;
  starts_after?: string;
  starts_before?: string;
}

export const matchesApi = {
  async list(query: MatchQuery = {}, options?: RequestOptions): Promise<ApiPage<Match>> {
    return (await apiClient.get<ApiPage<Match>>("/sports/fixtures", { ...options, query })).data;
  },
  async get(matchId: ResourceId, options?: RequestOptions): Promise<Match> {
    return (await apiClient.get<Match>(`/sports/fixtures/${matchId}`, options)).data;
  },
};
