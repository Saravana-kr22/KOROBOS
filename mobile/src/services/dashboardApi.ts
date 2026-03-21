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
    return apiClient.get<OverviewResponse>("/api/v1/dashboard/overview");
  },

  async getDaily(): Promise<DailyMetrics> {
    return apiClient.get<DailyMetrics>("/api/v1/dashboard/daily");
  },

  async getWeekly(): Promise<WeeklyResponse> {
    return apiClient.get<WeeklyResponse>("/api/v1/dashboard/weekly");
  },

  async getMetrics(): Promise<DailyMetrics> {
    return apiClient.get<DailyMetrics>("/api/v1/dashboard/metrics");
  },
};
