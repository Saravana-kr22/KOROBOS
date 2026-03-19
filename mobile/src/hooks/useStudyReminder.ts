/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Hook for scheduling and cancelling a daily study reminder using
 * expo-notifications local scheduling API.
 *
 * No server round-trip is required — the reminder fires locally on device.
 * This satisfies Sprint_9.md Section 15 "push reminders" for mobile.
 */

import * as Notifications from "expo-notifications";
import { useCallback, useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

const REMINDER_ID_KEY = "korobos:study_reminder_id";
const REMINDER_TIME_KEY = "korobos:study_reminder_time";

export interface StudyReminderState {
  isSet: boolean;
  hour: number | null;
  minute: number | null;
}

/**
 * Schedule (or reschedule) a daily study reminder at the given hour:minute.
 * Cancels any previously scheduled reminder first.
 */
async function scheduleStudyReminder(
  hour: number,
  minute: number,
): Promise<void> {
  // Request permissions if not already granted
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") {
    throw new Error("Notification permissions not granted");
  }

  // Cancel existing reminder
  const existingId = await AsyncStorage.getItem(REMINDER_ID_KEY);
  if (existingId) {
    await Notifications.cancelScheduledNotificationAsync(existingId);
  }

  // Schedule new daily repeating reminder
  const id = await Notifications.scheduleNotificationAsync({
    content: {
      title: "Time to learn! 📚",
      body: "Your daily study session is waiting. Open KOROBOS to get started.",
      sound: true,
    },
    trigger: {
      hour,
      minute,
      repeats: true,
    } as Notifications.DailyTriggerInput,
  });

  await AsyncStorage.setItem(REMINDER_ID_KEY, id);
  await AsyncStorage.setItem(
    REMINDER_TIME_KEY,
    JSON.stringify({ hour, minute }),
  );
}

/**
 * Cancel the currently scheduled study reminder, if any.
 */
async function cancelStudyReminder(): Promise<void> {
  const existingId = await AsyncStorage.getItem(REMINDER_ID_KEY);
  if (existingId) {
    await Notifications.cancelScheduledNotificationAsync(existingId);
    await AsyncStorage.removeItem(REMINDER_ID_KEY);
    await AsyncStorage.removeItem(REMINDER_TIME_KEY);
  }
}

/**
 * Hook that manages a daily study reminder.
 *
 * Returns:
 *  - reminderState: current reminder (isSet, hour, minute)
 *  - setReminder(hour, minute): schedule/reschedule
 *  - clearReminder(): cancel
 */
export function useStudyReminder() {
  const [reminderState, setReminderState] = useState<StudyReminderState>({
    isSet: false,
    hour: null,
    minute: null,
  });

  // Load persisted reminder state on mount
  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(REMINDER_TIME_KEY);
        if (raw) {
          const { hour, minute } = JSON.parse(raw);
          setReminderState({ isSet: true, hour, minute });
        }
      } catch {
        // ignore storage errors
      }
    })();
  }, []);

  const setReminder = useCallback(async (hour: number, minute: number) => {
    await scheduleStudyReminder(hour, minute);
    setReminderState({ isSet: true, hour, minute });
  }, []);

  const clearReminder = useCallback(async () => {
    await cancelStudyReminder();
    setReminderState({ isSet: false, hour: null, minute: null });
  }, []);

  return { reminderState, setReminder, clearReminder };
}
