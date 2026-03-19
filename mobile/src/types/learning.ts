/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * TypeScript types for the Learning Service (mobile).
 */

export interface Topic {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface TopicListResponse {
  topics: Topic[];
  total: number;
}

export interface LearningSession {
  id: string;
  user_id: string;
  topic: string;
  topic_id: string | null;
  duration: number; // minutes
  notes: string | null;
  status: "active" | "paused" | "completed";
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  updated_at: string;
}

export interface LearningSessionListResponse {
  sessions: LearningSession[];
  total: number;
}

export interface LearningStats {
  total_sessions: number;
  total_minutes: number;
  topics: string[];
  sessions_today: number;
  current_streak: number;
  weekly_minutes: number;
  topic_distribution: Record<string, number>;
}

export interface SessionStartPayload {
  topic: string;
  topic_id?: string;
  notes?: string;
}

export interface SessionStopPayload {
  session_id: string;
  notes?: string;
}

export interface SessionPausePayload {
  session_id: string;
}

export interface SessionResumePayload {
  session_id: string;
}

export interface SessionLogPayload {
  topic: string;
  duration: number;
  topic_id?: string;
  notes?: string;
}

export interface CreateTopicPayload {
  name: string;
}

export interface UpdateTopicPayload {
  name: string;
}
