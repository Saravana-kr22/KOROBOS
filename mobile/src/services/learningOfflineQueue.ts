/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Offline queue for learning sessions — stores pending manual logs when the
 * network is unavailable and syncs them when connectivity is restored.
 *
 * Timer sessions (start/stop) are NOT queued offline because they require
 * server-side time tracking. Only manual log entries are queued.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { SessionLogPayload } from "../types/learning";
import { learningApi } from "./learningApi";

const QUEUE_KEY = "korobos:learning_sessions_queue";

export interface PendingSessionLog {
  local_id: string;
  payload: SessionLogPayload;
  queued_at: string;
  synced: boolean;
}

/**
 * Add a pending session log to the offline queue.
 */
export async function queueSessionLog(
  payload: SessionLogPayload,
): Promise<PendingSessionLog> {
  const localId = `session-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 7)}`;
  const entry: PendingSessionLog = {
    local_id: localId,
    payload,
    queued_at: new Date().toISOString(),
    synced: false,
  };

  const pending = await getPendingSessionLogs();
  pending.push(entry);
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));
  return entry;
}

/**
 * Retrieve all pending session logs from the offline queue.
 */
export async function getPendingSessionLogs(): Promise<PendingSessionLog[]> {
  try {
    const data = await AsyncStorage.getItem(QUEUE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

/**
 * Count unsynced items in the offline queue.
 */
export async function getPendingCount(): Promise<number> {
  const pending = await getPendingSessionLogs();
  return pending.filter((e) => !e.synced).length;
}

/**
 * Sync all pending session logs to the server.
 * Returns the number of successfully synced items.
 */
export async function syncPendingSessionLogs(): Promise<number> {
  const pending = await getPendingSessionLogs();
  const unsynced = pending.filter((e) => !e.synced);

  let syncedCount = 0;

  for (const item of unsynced) {
    try {
      await learningApi.logSession(item.payload);
      item.synced = true;
      syncedCount++;
    } catch (error) {
      console.warn(`Failed to sync session log ${item.local_id}: ${error}`);
    }
  }

  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));
  return syncedCount;
}

/**
 * Remove all synced entries from the queue to keep storage lean.
 */
export async function clearSyncedLogs(): Promise<void> {
  const pending = await getPendingSessionLogs();
  const unsynced = pending.filter((e) => !e.synced);
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(unsynced));
}
