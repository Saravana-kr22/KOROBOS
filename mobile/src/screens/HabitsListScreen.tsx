/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Mobile screen — Today's Habits List with quick completion.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import * as SecureStore from "expo-secure-store";

import { habitsApi } from "../services/habitsApi";
import {
  queueCompletion,
  syncPendingCompletions,
} from "../services/offlineQueue";
import { HabitTodayItem } from "../types/habits";

export default function HabitsListScreen({ navigation }: { navigation: any }) {
  const [habits, setHabits] = useState<HabitTodayItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadHabits = useCallback(async () => {
    try {
      setError("");
      const token = await SecureStore.getItemAsync("auth_token");
      if (!token) {
        setError("Not authenticated");
        return;
      }

      const data = await habitsApi.getTodayHabits();
      setHabits(data.habits || []);
    } catch (err) {
      setError("Failed to load habits");
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHabits();
  }, [loadHabits]);

  useFocusEffect(
    useCallback(() => {
      // Sync pending completions when screen comes into focus
      syncPendingCompletions()
        .then((count) => {
          if (count > 0) {
            // Reload habits to reflect synced completions
            loadHabits();
          }
        })
        .catch((err) =>
          console.warn("Failed to sync pending completions:", err),
        );
    }, [loadHabits]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    loadHabits();
  };

  const handleMarkComplete = async (habitId: string, habitName: string) => {
    try {
      const result = await habitsApi.completeHabit(habitId);
      Alert.alert(
        "Success",
        `${habitName} marked as complete! Streak: ${result.streak}`,
      );
      await loadHabits();
    } catch (err) {
      // Offline fallback: queue the completion for later sync
      console.warn(
        "Network error marking habit complete, queueing for sync:",
        err,
      );
      try {
        await queueCompletion(habitId, habitName);
        Alert.alert(
          "Offline Mode",
          `${habitName} saved offline. Will sync when you're back online.`,
          [{ text: "OK" }],
        );
        // Update UI optimistically
        await loadHabits();
      } catch (queueErr) {
        Alert.alert("Error", "Failed to save habit completion");
      }
    }
  };

  const handleNavigateToHabitDetail = (habitId: string, habitName: string) => {
    navigation.navigate("HabitDetail", { habitId, habitName });
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : (
        <FlatList
          data={habits}
          keyExtractor={(item) => item.habit_id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.habitItem,
                item.completed && styles.habitItemCompleted,
              ]}
              onPress={() =>
                handleNavigateToHabitDetail(item.habit_id, item.name)
              }
            >
              <View style={styles.habitInfo}>
                <Text style={styles.habitName}>{item.name}</Text>
                {item.completed && (
                  <Text style={styles.completedBadge}>✓ Done</Text>
                )}
              </View>
              {!item.completed && (
                <TouchableOpacity
                  style={styles.completeButton}
                  onPress={() => handleMarkComplete(item.habit_id, item.name)}
                >
                  <Text style={styles.completeButtonText}>Complete</Text>
                </TouchableOpacity>
              )}
            </TouchableOpacity>
          )}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No habits for today</Text>
            </View>
          }
        />
      )}

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate("CreateHabit")}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  errorText: {
    color: "#dc3545",
    fontSize: 16,
  },
  habitItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 15,
    marginHorizontal: 10,
    marginVertical: 5,
    backgroundColor: "#fff",
    borderRadius: 8,
    borderColor: "#e0e0e0",
    borderWidth: 1,
  },
  habitItemCompleted: {
    backgroundColor: "#f0f8f0",
  },
  habitInfo: {
    flex: 1,
  },
  habitName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 4,
  },
  completedBadge: {
    color: "#28a745",
    fontSize: 14,
    fontWeight: "600",
  },
  completeButton: {
    backgroundColor: "#007bff",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  completeButtonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
    color: "#999",
  },
  fab: {
    position: "absolute",
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#007bff",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3,
    elevation: 5,
  },
  fabText: {
    color: "#fff",
    fontSize: 28,
    fontWeight: "bold",
  },
});
