/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * API client for the Habit Service (mobile/React Native).
 * Wraps the singleton apiClient to provide typed methods.
 */

import {
  CreateHabitPayload,
  Habit,
  HabitCompleteResponse,
  HabitListResponse,
  HabitStats,
  HabitTodayResponse,
  UpdateHabitPayload,
} from "../types/habits";
import { apiClient } from "./apiClient";

export const habitsApi = {
  /**
   * List all habits for the current user with pagination.
   */
  async listHabits(
    page: number = 1,
    limit: number = 50,
  ): Promise<HabitListResponse> {
    const offset = (page - 1) * limit;
    return apiClient.get<HabitListResponse>("/habits", {
      offset: String(offset),
      limit: String(limit),
    });
  },

  /**
   * Get today's active daily habits with completion status.
   */
  async getTodayHabits(): Promise<HabitTodayResponse> {
    return apiClient.get<HabitTodayResponse>("/habits/today");
  },

  /**
   * Get a single habit by ID.
   */
  async getHabit(id: string): Promise<Habit> {
    return apiClient.get<Habit>(`/habits/${id}`);
  },

  /**
   * Create a new habit.
   */
  async createHabit(data: CreateHabitPayload): Promise<Habit> {
    return apiClient.post<Habit>("/habits", data);
  },

  /**
   * Update an existing habit.
   */
  async updateHabit(id: string, data: UpdateHabitPayload): Promise<Habit> {
    return apiClient.put<Habit>(`/habits/${id}`, data);
  },

  /**
   * Delete a habit.
   */
  async deleteHabit(id: string): Promise<void> {
    return apiClient.delete<void>(`/habits/${id}`);
  },

  /**
   * Mark a habit as completed for today.
   */
  async completeHabit(id: string): Promise<HabitCompleteResponse> {
    return apiClient.post<HabitCompleteResponse>(`/habits/${id}/complete`);
  },

  /**
   * Get statistics for a habit.
   */
  async getStats(id: string): Promise<HabitStats> {
    return apiClient.get<HabitStats>(`/habits/${id}/stats`);
  },
};
