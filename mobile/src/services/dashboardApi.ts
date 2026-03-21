/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Dashboard API client for React Native.
 */

import {
  DailyMetrics,
  OverviewResponse,
  WeeklyResponse,
} from "../types/dashboard";
import { apiClient } from "./apiClient";

export const dashboardApi = {
  async getOverview(): Promise<OverviewResponse> {
    const response = await apiClient.get<OverviewResponse>(
      "/api/v1/dashboard/overview",
    );
    return response.data;
  },

  async getDaily(): Promise<DailyMetrics> {
    const response = await apiClient.get<DailyMetrics>(
      "/api/v1/dashboard/daily",
    );
    return response.data;
  },

  async getWeekly(): Promise<WeeklyResponse> {
    const response = await apiClient.get<WeeklyResponse>(
      "/api/v1/dashboard/weekly",
    );
    return response.data;
  },

  async getMetrics(): Promise<DailyMetrics> {
    const response = await apiClient.get<DailyMetrics>(
      "/api/v1/dashboard/metrics",
    );
    return response.data;
  },
};
