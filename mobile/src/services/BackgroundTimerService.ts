/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Service for managing persistent background notifications during active learning timers.
 * Displays a notification in the device notification tray when the app is backgrounded with
 * an active timer session.
 */

import * as Notifications from "expo-notifications";
import AsyncStorage from "@react-native-async-storage/async-storage";

const TIMER_NOTIFICATION_ID_KEY = "korobos:timer_notification_id";

/**
 * Format elapsed seconds into H:MM:SS or M:SS format.
 */
function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
    : `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * Show a persistent background notification for an active timer session.
 * Cancels any previously scheduled timer notification before showing the new one.
 *
 * @param topic - The learning topic name
 * @param elapsedSeconds - Elapsed time in seconds
 */
export async function showTimerNotification(
  topic: string,
  elapsedSeconds: number,
): Promise<void> {
  try {
    // Cancel any existing timer notification
    await cancelTimerNotification();

    // Request notification permissions if not already granted
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== "granted") {
      console.warn("Notification permissions not granted");
      return;
    }

    // Schedule immediate notification with persistent content
    const notificationId = await Notifications.scheduleNotificationAsync({
      content: {
        title: "KOROBOS Timer Running 📚",
        body: `${topic} — ${formatElapsed(elapsedSeconds)}`,
        sound: true,
      },
      trigger: null, // Immediate notification
    });

    // Store notification ID for later cancellation
    await AsyncStorage.setItem(TIMER_NOTIFICATION_ID_KEY, notificationId);
  } catch (error) {
    console.error("Error showing timer notification:", error);
  }
}

/**
 * Update the current timer notification with new elapsed time.
 * Used to keep the notification content fresh as the timer progresses.
 *
 * @param topic - The learning topic name
 * @param elapsedSeconds - Elapsed time in seconds
 */
export async function updateTimerNotification(
  topic: string,
  elapsedSeconds: number,
): Promise<void> {
  try {
    // Cancel and reschedule to update content
    await cancelTimerNotification();
    await showTimerNotification(topic, elapsedSeconds);
  } catch (error) {
    console.error("Error updating timer notification:", error);
  }
}

/**
 * Cancel the currently active timer notification.
 * Called when the app returns to foreground or when the session stops/pauses.
 */
export async function cancelTimerNotification(): Promise<void> {
  try {
    const notificationId = await AsyncStorage.getItem(
      TIMER_NOTIFICATION_ID_KEY,
    );
    if (notificationId) {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
      await AsyncStorage.removeItem(TIMER_NOTIFICATION_ID_KEY);
    }
  } catch (error) {
    console.error("Error cancelling timer notification:", error);
  }
}
