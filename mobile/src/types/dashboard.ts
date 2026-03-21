export interface DailyMetrics {
  date: string;
  habits_completed: number;
  total_habits: number;
  learning_minutes: number;
  calories_consumed: number;
  calories_burned: number;
  net_calories: number;
  productivity_score: number;
}

export interface OverviewResponse {
  date: string;
  habits_completed: number;
  learning_minutes: number;
  calories_balance: number;
  productivity_score: number;
}

export interface WeeklyResponse {
  week_start: string;
  week_end: string;
  days: DailyMetrics[];
  avg_productivity_score: number;
  total_learning_minutes: number;
  avg_habits_completed: number;
}
