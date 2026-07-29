import { apiClient, type RequestOptions } from "./client";
import type { ApiPage, PaginationParams } from "@/types/api";
import type { DatasetSnapshot, Experiment, Hypothesis } from "@/types/domain";

export const researchApi = {
  async listDatasets(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<DatasetSnapshot>> {
    return (
      await apiClient.get<ApiPage<DatasetSnapshot>>("/research/datasets", { ...options, query })
    ).data;
  },
  async listExperiments(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<Experiment>> {
    return (
      await apiClient.get<ApiPage<Experiment>>("/research/experiments", { ...options, query })
    ).data;
  },
  async listHypotheses(
    query: PaginationParams = {},
    options?: RequestOptions,
  ): Promise<ApiPage<Hypothesis>> {
    return (await apiClient.get<ApiPage<Hypothesis>>("/research/hypotheses", { ...options, query }))
      .data;
  },
};
