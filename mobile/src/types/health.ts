/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * TypeScript types for the Health Service.
 */

export interface HealthLog {
  id: string;
  user_id: string;
  log_type: "meal" | "workout";
  calories: number | null;
  duration: number | null;
  description: string | null;
  food_name: string | null;
  workout_type: string | null;
  protein: number | null;
  carbs: number | null;
  fat: number | null;
  created_at: string;
  updated_at: string;
}

export interface HealthLogListResponse {
  logs: HealthLog[];
  total: number;
}

export interface HealthStatsResponse {
  total_meals: number;
  total_workouts: number;
  total_calories: number;
  total_workout_minutes: number;
}

export interface DailyStatsResponse {
  calories_consumed: number;
  calories_burned: number;
  net_calories: number;
}

export interface LogMealPayload {
  calories: number;
  food_name?: string;
  protein?: number;
  carbs?: number;
  fat?: number;
  description?: string;
}

export interface LogWorkoutPayload {
  duration: number;
  workout_type?: string;
  calories?: number;
  description?: string;
}
