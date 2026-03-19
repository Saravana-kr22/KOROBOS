/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * API client for the Learning Service (mobile/React Native).
 */

import {
  CreateTopicPayload,
  LearningSession,
  LearningSessionListResponse,
  LearningStats,
  SessionLogPayload,
  SessionPausePayload,
  SessionResumePayload,
  SessionStartPayload,
  SessionStopPayload,
  Topic,
  TopicListResponse,
  UpdateTopicPayload,
} from "../types/learning";
import { apiClient } from "./apiClient";

export const learningApi = {
  // ---------------------------------------------------------------------------
  // Topics
  // ---------------------------------------------------------------------------

  async listTopics(): Promise<TopicListResponse> {
    return apiClient.get<TopicListResponse>("/learning/topics");
  },

  async createTopic(data: CreateTopicPayload): Promise<Topic> {
    return apiClient.post<Topic>("/learning/topics", data);
  },

  async updateTopic(id: string, data: UpdateTopicPayload): Promise<Topic> {
    return apiClient.put<Topic>(`/learning/topics/${id}`, data);
  },

  async deleteTopic(id: string): Promise<void> {
    return apiClient.delete<void>(`/learning/topics/${id}`);
  },

  // ---------------------------------------------------------------------------
  // Timer
  // ---------------------------------------------------------------------------

  async startSession(data: SessionStartPayload): Promise<LearningSession> {
    return apiClient.post<LearningSession>("/learning/session/start", data);
  },

  async stopSession(data: SessionStopPayload): Promise<LearningSession> {
    return apiClient.post<LearningSession>("/learning/session/stop", data);
  },

  async pauseSession(data: SessionPausePayload): Promise<LearningSession> {
    return apiClient.post<LearningSession>("/learning/session/pause", data);
  },

  async resumeSession(data: SessionResumePayload): Promise<LearningSession> {
    return apiClient.post<LearningSession>("/learning/session/resume", data);
  },

  // ---------------------------------------------------------------------------
  // Manual log
  // ---------------------------------------------------------------------------

  async logSession(data: SessionLogPayload): Promise<LearningSession> {
    return apiClient.post<LearningSession>("/learning/session/log", data);
  },

  // ---------------------------------------------------------------------------
  // Sessions
  // ---------------------------------------------------------------------------

  async listSessions(
    offset: number = 0,
    limit: number = 20,
  ): Promise<LearningSessionListResponse> {
    return apiClient.get<LearningSessionListResponse>("/learning/sessions", {
      offset: String(offset),
      limit: String(limit),
    });
  },

  async getSession(id: string): Promise<LearningSession> {
    return apiClient.get<LearningSession>(`/learning/sessions/${id}`);
  },

  async deleteSession(id: string): Promise<void> {
    return apiClient.delete<void>(`/learning/sessions/${id}`);
  },

  // ---------------------------------------------------------------------------
  // Note linking
  // ---------------------------------------------------------------------------

  async getSessionNotes(sessionId: string): Promise<string[]> {
    const data = await apiClient.get<{
      session_id: string;
      note_ids: string[];
    }>(`/learning/sessions/${sessionId}/notes`);
    return data.note_ids;
  },

  async linkNote(sessionId: string, noteId: string): Promise<void> {
    return apiClient.post<void>(`/learning/sessions/${sessionId}/notes`, {
      note_id: noteId,
    });
  },

  async unlinkNote(sessionId: string, noteId: string): Promise<void> {
    return apiClient.delete<void>(
      `/learning/sessions/${sessionId}/notes/${noteId}`,
    );
  },

  // ---------------------------------------------------------------------------
  // Analytics
  // ---------------------------------------------------------------------------

  async getStats(): Promise<LearningStats> {
    return apiClient.get<LearningStats>("/learning/stats");
  },
};
