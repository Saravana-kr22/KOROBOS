/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Offline queue for storing pending health logs when the network is unavailable.
 * Uses AsyncStorage to persist the queue across app restarts.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { healthApi } from "./healthApi";
import { LogMealPayload, LogWorkoutPayload } from "../types/health";

const QUEUE_KEY = "korobos:health_logs_queue";

export interface PendingHealthLog {
  local_id: string;
  log_type: "meal" | "workout";
  payload: LogMealPayload | LogWorkoutPayload;
  queued_at: string;
  synced: boolean;
}

/**
 * Add a pending health log to the offline queue.
 */
export async function queueHealthLog(
  logType: "meal" | "workout",
  payload: LogMealPayload | LogWorkoutPayload,
): Promise<PendingHealthLog> {
  const localId = `${logType}-${Date.now()}`;
  const log: PendingHealthLog = {
    local_id: localId,
    log_type: logType,
    payload,
    queued_at: new Date().toISOString(),
    synced: false,
  };

  const pending = await getPendingLogs();
  pending.push(log);

  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));
  return log;
}

/**
 * Get all pending health logs from the offline queue.
 */
export async function getPendingLogs(): Promise<PendingHealthLog[]> {
  try {
    const data = await AsyncStorage.getItem(QUEUE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

/**
 * Sync all pending health logs to the server.
 * Returns the number of successfully synced items.
 */
export async function syncPendingLogs(): Promise<number> {
  const pending = await getPendingLogs();
  const unsynced = pending.filter((l) => !l.synced);

  let syncedCount = 0;

  for (const item of unsynced) {
    try {
      if (item.log_type === "meal") {
        await healthApi.logMeal(item.payload as LogMealPayload);
      } else {
        await healthApi.logWorkout(item.payload as LogWorkoutPayload);
      }
      item.synced = true;
      syncedCount++;
    } catch (error) {
      // Swallow error — retry next time
      console.warn(`Failed to sync health log ${item.local_id}: ${error}`);
    }
  }

  // Update queue with synced status
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));

  return syncedCount;
}

/**
 * Clear all synced health logs from the offline queue.
 */
export async function clearSynced(): Promise<void> {
  const pending = await getPendingLogs();
  const unsynced = pending.filter((l) => !l.synced);
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(unsynced));
}
