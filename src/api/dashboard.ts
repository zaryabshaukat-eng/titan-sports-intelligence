import { apiClient, type RequestOptions } from "./client";
import type { DashboardSnapshot } from "@/types/domain";

/** Dashboard is reserved for the Phase 3.2 read model. */
export const dashboardApi = {
  async get(options?: RequestOptions): Promise<DashboardSnapshot> {
    return (await apiClient.get<DashboardSnapshot>("/dashboard", options)).data;
  },
};
