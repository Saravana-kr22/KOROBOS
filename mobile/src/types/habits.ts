/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * TypeScript types for the Habit Service.
 */

export interface Habit {
  id: string;
  user_id: string;
  name: string;
  frequency: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HabitListResponse {
  habits: Habit[];
  total: number;
}

export interface HabitTodayItem {
  habit_id: string;
  name: string;
  completed: boolean;
}

export interface HabitTodayResponse {
  habits: HabitTodayItem[];
}

export interface HabitCompleteResponse {
  habit_id: string;
  completed: boolean;
  streak: number;
}

export interface HabitStats {
  habit_id: string;
  completion_rate: number;
  current_streak: number;
  longest_streak: number;
  weekly_consistency: number;
}

export interface CreateHabitPayload {
  name: string;
  frequency?: string;
  description?: string;
  is_active?: boolean;
}

export interface UpdateHabitPayload {
  name?: string;
  frequency?: string;
  description?: string;
  is_active?: boolean;
}
