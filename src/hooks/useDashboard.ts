import { queryOptions, useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/dashboard";
import { queryKeys } from "@/api/query-keys";

export const dashboardQueryOptions = () =>
  queryOptions({ queryKey: queryKeys.dashboard, queryFn: () => dashboardApi.get() });

export const useDashboard = () => useQuery(dashboardQueryOptions());
