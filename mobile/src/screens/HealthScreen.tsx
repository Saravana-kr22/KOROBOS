/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Health tracking screen for mobile (React Native).
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  FlatList,
  Dimensions,
  Pressable,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { healthApi } from "../services/healthApi";
import {
  syncPendingLogs,
  getPendingLogs,
  queueHealthLog,
} from "../services/healthOfflineQueue";
import {
  DailyStatsResponse,
  HealthLog,
  LogMealPayload,
  LogWorkoutPayload,
} from "../types/health";

const HealthScreen = () => {
  const [dailyStats, setDailyStats] = useState<DailyStatsResponse | null>(null);
  const [logs, setLogs] = useState<HealthLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"meals" | "workouts">("meals");

  // Meal form state
  const [mealForm, setMealForm] = useState({
    food_name: "",
    calories: "",
    protein: "",
    carbs: "",
    fat: "",
  });

  // Workout form state
  const [workoutForm, setWorkoutForm] = useState({
    workout_type: "",
    duration: "",
    calories: "",
  });

  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    try {
      // Load daily stats
      const stats = await healthApi.getDailyStats();
      setDailyStats(stats);

      // Load recent logs
      const response = await healthApi.listLogs(undefined, 1, 20);
      setLogs(response.logs);

      // Try to sync pending logs
      if (isOnline) {
        await syncPendingLogs();
      }

      // Update pending count
      const pending = await getPendingLogs();
      setPendingCount(pending.filter((l) => !l.synced).length);
    } catch (err: any) {
      // Network error — likely offline
      setIsOnline(false);
      console.warn("Failed to load health data:", err.message);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useFocusEffect(
    useCallback(() => {
      loadHealth();
    }, [loadHealth]),
  );

  const handleLogMeal = async () => {
    if (!mealForm.calories.trim()) {
      Alert.alert("Validation", "Calories is required");
      return;
    }

    const payload: LogMealPayload = {
      calories: parseInt(mealForm.calories),
      food_name: mealForm.food_name || undefined,
      protein: mealForm.protein ? parseInt(mealForm.protein) : undefined,
      carbs: mealForm.carbs ? parseInt(mealForm.carbs) : undefined,
      fat: mealForm.fat ? parseInt(mealForm.fat) : undefined,
    };

    try {
      await healthApi.logMeal(payload);
      setMealForm({
        food_name: "",
        calories: "",
        protein: "",
        carbs: "",
        fat: "",
      });
      setIsOnline(true);
      await loadHealth();
    } catch (err: any) {
      // Log offline
      await queueHealthLog("meal", payload);
      setIsOnline(false);
      Alert.alert("Offline", "Meal logged locally and will sync when online");
      setMealForm({
        food_name: "",
        calories: "",
        protein: "",
        carbs: "",
        fat: "",
      });
      await loadHealth();
    }
  };

  const handleLogWorkout = async () => {
    if (!workoutForm.duration.trim()) {
      Alert.alert("Validation", "Duration is required");
      return;
    }

    const payload: LogWorkoutPayload = {
      duration: parseInt(workoutForm.duration),
      workout_type: workoutForm.workout_type || undefined,
      calories: workoutForm.calories
        ? parseInt(workoutForm.calories)
        : undefined,
    };

    try {
      await healthApi.logWorkout(payload);
      setWorkoutForm({ workout_type: "", duration: "", calories: "" });
      setIsOnline(true);
      await loadHealth();
    } catch (err: any) {
      // Log offline
      await queueHealthLog("workout", payload);
      setIsOnline(false);
      Alert.alert(
        "Offline",
        "Workout logged locally and will sync when online",
      );
      setWorkoutForm({ workout_type: "", duration: "", calories: "" });
      await loadHealth();
    }
  };

  const deleteLog = async (logId: string) => {
    Alert.alert("Delete Log", "Are you sure?", [
      { text: "Cancel" },
      {
        text: "Delete",
        onPress: async () => {
          try {
            await healthApi.deleteLog(logId);
            await loadHealth();
          } catch (err) {
            Alert.alert("Error", "Failed to delete log");
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header with sync status */}
      <View style={styles.header}>
        <Text style={styles.title}>Health Tracking</Text>
        {!isOnline && (
          <View style={styles.offlineBadge}>
            <Text style={styles.offlineText}>Offline</Text>
          </View>
        )}
        {pendingCount > 0 && (
          <Text style={styles.pendingText}>{pendingCount} pending syncs</Text>
        )}
      </View>

      {/* Daily Summary */}
      {dailyStats && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Today&apos;s Summary</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>
                {dailyStats.calories_consumed}
              </Text>
              <Text style={styles.statLabel}>Consumed (kcal)</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>{dailyStats.calories_burned}</Text>
              <Text style={styles.statLabel}>Burned (kcal)</Text>
            </View>
            <View style={styles.statBox}>
              <Text
                style={[
                  styles.statValue,
                  {
                    color: dailyStats.net_calories > 0 ? "#dc3545" : "#28a745",
                  },
                ]}
              >
                {dailyStats.net_calories}
              </Text>
              <Text style={styles.statLabel}>Net (kcal)</Text>
            </View>
          </View>
        </View>
      )}

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <Pressable
          onPress={() => setActiveTab("meals")}
          style={[styles.tab, activeTab === "meals" && styles.activeTab]}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === "meals" && styles.activeTabText,
            ]}
          >
            Log Meal
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setActiveTab("workouts")}
          style={[styles.tab, activeTab === "workouts" && styles.activeTab]}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === "workouts" && styles.activeTabText,
            ]}
          >
            Log Workout
          </Text>
        </Pressable>
      </View>

      {/* Meal Form */}
      {activeTab === "meals" && (
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Log Meal</Text>
          <TextInput
            placeholder="Food name (optional)"
            value={mealForm.food_name}
            onChangeText={(text) =>
              setMealForm({ ...mealForm, food_name: text })
            }
            style={styles.input}
          />
          <TextInput
            placeholder="Calories (required)"
            keyboardType="number-pad"
            value={mealForm.calories}
            onChangeText={(text) =>
              setMealForm({ ...mealForm, calories: text })
            }
            style={styles.input}
          />
          <View style={styles.row}>
            <TextInput
              placeholder="Protein (g)"
              keyboardType="number-pad"
              value={mealForm.protein}
              onChangeText={(text) =>
                setMealForm({ ...mealForm, protein: text })
              }
              style={[styles.input, { flex: 1, marginRight: 8 }]}
            />
            <TextInput
              placeholder="Carbs (g)"
              keyboardType="number-pad"
              value={mealForm.carbs}
              onChangeText={(text) => setMealForm({ ...mealForm, carbs: text })}
              style={[styles.input, { flex: 1, marginRight: 8 }]}
            />
            <TextInput
              placeholder="Fat (g)"
              keyboardType="number-pad"
              value={mealForm.fat}
              onChangeText={(text) => setMealForm({ ...mealForm, fat: text })}
              style={[styles.input, { flex: 1 }]}
            />
          </View>
          <TouchableOpacity onPress={handleLogMeal} style={styles.button}>
            <Text style={styles.buttonText}>Log Meal</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Workout Form */}
      {activeTab === "workouts" && (
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Log Workout</Text>
          <TextInput
            placeholder="Workout type (e.g., Running)"
            value={workoutForm.workout_type}
            onChangeText={(text) =>
              setWorkoutForm({ ...workoutForm, workout_type: text })
            }
            style={styles.input}
          />
          <TextInput
            placeholder="Duration (minutes, required)"
            keyboardType="number-pad"
            value={workoutForm.duration}
            onChangeText={(text) =>
              setWorkoutForm({ ...workoutForm, duration: text })
            }
            style={styles.input}
          />
          <TextInput
            placeholder="Calories burned (optional)"
            keyboardType="number-pad"
            value={workoutForm.calories}
            onChangeText={(text) =>
              setWorkoutForm({ ...workoutForm, calories: text })
            }
            style={styles.input}
          />
          <TouchableOpacity onPress={handleLogWorkout} style={styles.button}>
            <Text style={styles.buttonText}>Log Workout</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Recent Logs */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Logs ({logs.length})</Text>
        {logs.length === 0 ? (
          <Text style={styles.emptyText}>No logs yet</Text>
        ) : (
          <FlatList
            data={logs}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            renderItem={({ item }) => (
              <View style={styles.logItem}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.logTitle}>
                    {item.log_type === "meal"
                      ? `🍽️ ${item.food_name || "Meal"}`
                      : `💪 ${item.workout_type || "Workout"}`}
                  </Text>
                  <Text style={styles.logDetails}>
                    {item.log_type === "meal"
                      ? `${item.calories} kcal`
                      : `${item.duration} min ${
                          item.calories ? `(${item.calories} kcal)` : ""
                        }`}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => deleteLog(item.id)}
                  style={styles.deleteButton}
                >
                  <Text style={styles.deleteButtonText}>✕</Text>
                </TouchableOpacity>
              </View>
            )}
          />
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  header: {
    padding: 16,
    paddingTop: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 8,
  },
  offlineBadge: {
    backgroundColor: "#ffc107",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: "flex-start",
  },
  offlineText: {
    fontSize: 12,
    fontWeight: "600",
  },
  pendingText: {
    fontSize: 12,
    color: "#666",
    marginTop: 4,
  },
  summaryCard: {
    backgroundColor: "#f8f9fa",
    margin: 16,
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#dee2e6",
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: "row",
    justifyContent: "space-around",
  },
  statBox: {
    alignItems: "center",
  },
  statValue: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#007bff",
  },
  statLabel: {
    fontSize: 12,
    color: "#666",
    marginTop: 4,
  },
  tabContainer: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginVertical: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginHorizontal: 4,
    borderRadius: 4,
    backgroundColor: "#f0f0f0",
  },
  activeTab: {
    backgroundColor: "#007bff",
  },
  tabText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#333",
    textAlign: "center",
  },
  activeTabText: {
    color: "#fff",
  },
  formCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    backgroundColor: "#f9f9f9",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ddd",
  },
  formTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 4,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 10,
    fontSize: 14,
  },
  row: {
    flexDirection: "row",
    marginBottom: 10,
  },
  button: {
    backgroundColor: "#28a745",
    paddingVertical: 12,
    borderRadius: 4,
    alignItems: "center",
    marginTop: 8,
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 14,
  },
  section: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
  },
  emptyText: {
    color: "#999",
  },
  logItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: "#eee",
    borderRadius: 6,
    marginBottom: 8,
    backgroundColor: "#fafafa",
  },
  logTitle: {
    fontWeight: "600",
    fontSize: 14,
    marginBottom: 4,
  },
  logDetails: {
    fontSize: 12,
    color: "#666",
  },
  deleteButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#dc3545",
    borderRadius: 4,
  },
  deleteButtonText: {
    color: "#fff",
    fontWeight: "600",
  },
});

export default HealthScreen;
