/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Offline queue for storing pending habit completions when the network is unavailable.
 * Uses AsyncStorage to persist the queue across app restarts.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { habitsApi } from "./habitsApi";

const QUEUE_KEY = "korobos:habit_completions_queue";

export interface PendingCompletion {
  local_id: string;
  habit_id: string;
  habit_name: string;
  queued_at: string;
  synced: boolean;
}

/**
 * Add a pending habit completion to the offline queue.
 */
export async function queueCompletion(
  habitId: string,
  habitName: string,
): Promise<PendingCompletion> {
  const localId = `${habitId}-${Date.now()}`;
  const completion: PendingCompletion = {
    local_id: localId,
    habit_id: habitId,
    habit_name: habitName,
    queued_at: new Date().toISOString(),
    synced: false,
  };

  const pending = await getPendingCompletions();
  pending.push(completion);

  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));
  return completion;
}

/**
 * Get all pending completions from the offline queue.
 */
export async function getPendingCompletions(): Promise<PendingCompletion[]> {
  try {
    const data = await AsyncStorage.getItem(QUEUE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

/**
 * Sync all pending completions to the server.
 * Returns the number of successfully synced items.
 */
export async function syncPendingCompletions(): Promise<number> {
  const pending = await getPendingCompletions();
  const unsynced = pending.filter((c) => !c.synced);

  let syncedCount = 0;

  for (const item of unsynced) {
    try {
      await habitsApi.completeHabit(item.habit_id);
      item.synced = true;
      syncedCount++;
    } catch (error) {
      // Swallow error — retry next time
      console.warn(`Failed to sync completion ${item.local_id}: ${error}`);
    }
  }

  // Update queue with synced status
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(pending));

  return syncedCount;
}

/**
 * Clear all synced completions from the offline queue.
 */
export async function clearSynced(): Promise<void> {
  const pending = await getPendingCompletions();
  const unsynced = pending.filter((c) => !c.synced);
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(unsynced));
}
