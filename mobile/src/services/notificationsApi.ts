/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * API client for the Notification Service (mobile/React Native).
 */

import { apiClient } from "./apiClient";

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  channel: string;
  is_read: boolean;
  created_at?: string;
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
  total: number;
}

export const notificationsApi = {
  /**
   * Register or update a push token for the current user.
   */
  async registerPushToken(token: string, platform: string): Promise<void> {
    return apiClient.post<void>("/notifications/push-token", {
      token,
      platform,
    });
  },

  /**
   * Get all notifications for the current user.
   */
  async listNotifications(
    limit: number = 50,
    offset: number = 0,
  ): Promise<NotificationListResponse> {
    return apiClient.get<NotificationListResponse>("/notifications", {
      limit: String(limit),
      offset: String(offset),
    });
  },

  /**
   * Mark a notification as read.
   */
  async markRead(id: string): Promise<void> {
    return apiClient.put<void>(`/notifications/${id}/read`, {});
  },
};
