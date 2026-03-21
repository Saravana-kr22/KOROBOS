/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * API client for the Health Service (mobile/React Native).
 * Wraps the singleton apiClient to provide typed methods.
 */

import {
  DailyStatsResponse,
  HealthLogListResponse,
  HealthStatsResponse,
  LogMealPayload,
  LogWorkoutPayload,
  HealthLog,
} from "../types/health";
import { apiClient } from "./apiClient";

export const healthApi = {
  /**
   * Log a meal with nutrition data.
   */
  async logMeal(data: LogMealPayload): Promise<HealthLog> {
    return apiClient.post<HealthLog>("/health/meals", data);
  },

  /**
   * Log a workout.
   */
  async logWorkout(data: LogWorkoutPayload): Promise<HealthLog> {
    return apiClient.post<HealthLog>("/health/workouts", data);
  },

  /**
   * List all health logs with optional filtering.
   */
  async listLogs(
    logType?: string,
    page: number = 1,
    limit: number = 50,
  ): Promise<HealthLogListResponse> {
    const offset = (page - 1) * limit;
    const params: Record<string, string> = {
      offset: String(offset),
      limit: String(limit),
    };
    if (logType) {
      params.log_type = logType;
    }
    return apiClient.get<HealthLogListResponse>("/health/logs", params);
  },

  /**
   * Get lifetime health statistics.
   */
  async getStats(): Promise<HealthStatsResponse> {
    return apiClient.get<HealthStatsResponse>("/health/stats");
  },

  /**
   * Get daily calorie statistics for a given date.
   */
  async getDailyStats(date?: string): Promise<DailyStatsResponse> {
    const params: Record<string, string> = {};
    if (date) {
      params.date = date;
    }
    return apiClient.get<DailyStatsResponse>("/health/daily", params);
  },

  /**
   * Delete a health log.
   */
  async deleteLog(logId: string): Promise<void> {
    return apiClient.delete<void>(`/health/logs/${logId}`);
  },
};
