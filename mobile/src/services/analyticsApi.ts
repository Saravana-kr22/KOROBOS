/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Analytics API client for React Native.
 */

import { apiClient } from "./apiClient";

export interface HabitMetrics {
  completion_rate: number;
  current_streak: number;
}

export interface HealthMetrics {
  intake: number;
  burned: number;
  balance: number;
}

export interface LearningMetrics {
  productivity_score: number;
  habit_consistency: number;
  learning_hours: number;
}

export interface KnowledgeMetrics {
  notes_created: number;
  records_created: number;
}

export interface AnalyticsOverview {
  productivity_score: number;
  habits: HabitMetrics;
  learning: LearningMetrics;
  health: HealthMetrics;
  knowledge: KnowledgeMetrics;
}

export interface TrendData {
  metric_type: string;
  values: number[];
  labels: string[];
}

export interface HealthAnalytics {
  current: HealthMetrics;
  intake_trend: TrendData;
  burned_trend: TrendData;
}

export interface AllTrends {
  habits: TrendData;
  learning: TrendData;
  health_intake: TrendData;
  health_burned: TrendData;
  notes: TrendData;
  records: TrendData;
}

export const analyticsApi = {
  async getOverview(): Promise<AnalyticsOverview> {
    const response = await apiClient.get<{ data: AnalyticsOverview }>(
      "/analytics/overview",
    );
    return response.data;
  },

  async getProductivity(): Promise<LearningMetrics> {
    const response = await apiClient.get<{ data: LearningMetrics }>(
      "/analytics/productivity",
    );
    return response.data;
  },

  async getHealth(
    limit: number = 30,
    offset: number = 0,
  ): Promise<HealthAnalytics> {
    const response = await apiClient.get<{ data: HealthAnalytics }>(
      `/analytics/health?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },

  async getHabits(limit: number = 30, offset: number = 0): Promise<TrendData> {
    const response = await apiClient.get<{ data: TrendData }>(
      `/analytics/habits?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },

  async getLearning(
    limit: number = 30,
    offset: number = 0,
  ): Promise<TrendData> {
    const response = await apiClient.get<{ data: TrendData }>(
      `/analytics/learning?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },

  async getTrends(
    period: "7d" | "30d" | "90d" = "7d",
    limit: number = 30,
    offset: number = 0,
  ): Promise<AllTrends> {
    const response = await apiClient.get<{ data: AllTrends }>(
      `/analytics/trends?period=${period}&limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },
};
