/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Mobile screen — Habit Detail with stats and quick actions.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { habitsApi } from "../services/habitsApi";
import { Habit, HabitStats } from "../types/habits";

export default function HabitDetailScreen({
  route,
  navigation,
}: {
  route: any;
  navigation: any;
}) {
  const { habitId } = route.params;
  const [habit, setHabit] = useState<Habit | null>(null);
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: "",
    frequency: "",
    description: "",
  });
  const [error, setError] = useState("");

  const loadHabitDetail = useCallback(async () => {
    try {
      setError("");
      const habitData = await habitsApi.getHabit(habitId);
      setHabit(habitData);
      setEditData({
        name: habitData.name,
        frequency: habitData.frequency,
        description: habitData.description || "",
      });

      const statsData = await habitsApi.getStats(habitId);
      setStats(statsData);
    } catch (err) {
      setError("Failed to load habit");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [habitId]);

  useEffect(() => {
    loadHabitDetail();
  }, [loadHabitDetail]);

  const handleMarkComplete = async () => {
    try {
      const result = await habitsApi.completeHabit(habitId);
      Alert.alert(
        "Success",
        `Habit marked as complete! Streak: ${result.streak}`,
      );
      await loadHabitDetail();
    } catch (err) {
      Alert.alert("Error", "Failed to mark habit complete");
    }
  };

  const handleSaveEdit = async () => {
    try {
      const updated = await habitsApi.updateHabit(habitId, {
        name: editData.name,
        frequency: editData.frequency,
        description: editData.description || undefined,
      });
      setHabit(updated);
      setEditing(false);
      Alert.alert("Success", "Habit updated");
    } catch (err) {
      Alert.alert("Error", "Failed to update habit");
    }
  };

  const handleDelete = () => {
    Alert.alert("Delete Habit", "Are you sure you want to delete this habit?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await habitsApi.deleteHabit(habitId);
            Alert.alert("Success", "Habit deleted");
            navigation.goBack();
          } catch (err) {
            Alert.alert("Error", "Failed to delete habit");
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

  if (!habit) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error || "Habit not found"}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      {editing ? (
        <View style={styles.editSection}>
          <Text style={styles.sectionTitle}>Edit Habit</Text>

          <Text style={styles.label}>Habit Name</Text>
          <TextInput
            style={styles.input}
            value={editData.name}
            onChangeText={(text) => setEditData({ ...editData, name: text })}
            placeholder="Habit name"
          />

          <Text style={styles.label}>Frequency</Text>
          <View style={styles.frequencyContainer}>
            {["daily", "weekly", "custom"].map((freq) => (
              <TouchableOpacity
                key={freq}
                style={[
                  styles.frequencyButton,
                  editData.frequency === freq && styles.frequencyButtonActive,
                ]}
                onPress={() => setEditData({ ...editData, frequency: freq })}
              >
                <Text
                  style={[
                    styles.frequencyButtonText,
                    editData.frequency === freq &&
                      styles.frequencyButtonTextActive,
                  ]}
                >
                  {freq.charAt(0).toUpperCase() + freq.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Description</Text>
          <TextInput
            style={[styles.input, { height: 100 }]}
            value={editData.description}
            onChangeText={(text) =>
              setEditData({ ...editData, description: text })
            }
            placeholder="Description (optional)"
            multiline
          />

          <TouchableOpacity style={styles.saveButton} onPress={handleSaveEdit}>
            <Text style={styles.saveButtonText}>Save Changes</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => setEditing(false)}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View>
          <Text style={styles.title}>{habit.name}</Text>

          <View style={styles.infoSection}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Frequency:</Text>
              <Text style={styles.infoValue}>
                {habit.frequency.charAt(0).toUpperCase() +
                  habit.frequency.slice(1)}
              </Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Status:</Text>
              <Text style={styles.infoValue}>
                {habit.is_active ? "Active" : "Inactive"}
              </Text>
            </View>
            {habit.description && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Description:</Text>
                <Text style={styles.infoValue}>{habit.description}</Text>
              </View>
            )}
          </View>

          {stats && (
            <View style={styles.statsSection}>
              <Text style={styles.sectionTitle}>Statistics</Text>

              <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                  <Text style={styles.statLabel}>Current Streak</Text>
                  <Text style={styles.statValue}>{stats.current_streak}</Text>
                </View>

                <View style={styles.statCard}>
                  <Text style={styles.statLabel}>Longest Streak</Text>
                  <Text style={styles.statValue}>{stats.longest_streak}</Text>
                </View>

                <View style={styles.statCard}>
                  <Text style={styles.statLabel}>Completion Rate</Text>
                  <Text style={styles.statValue}>
                    {(stats.completion_rate * 100).toFixed(1)}%
                  </Text>
                </View>

                <View style={styles.statCard}>
                  <Text style={styles.statLabel}>Weekly Consistency</Text>
                  <Text style={styles.statValue}>
                    {(stats.weekly_consistency * 100).toFixed(1)}%
                  </Text>
                </View>
              </View>
            </View>
          )}

          <View style={styles.actionsSection}>
            <TouchableOpacity
              style={styles.completeButton}
              onPress={handleMarkComplete}
            >
              <Text style={styles.completeButtonText}>Mark Complete Today</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.editButton}
              onPress={() => setEditing(true)}
            >
              <Text style={styles.editButtonText}>Edit</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.deleteButton}
              onPress={handleDelete}
            >
              <Text style={styles.deleteButtonText}>Delete</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
    padding: 15,
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 15,
  },
  infoSection: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
    borderColor: "#e0e0e0",
    borderWidth: 1,
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 14,
    color: "#666",
    fontWeight: "600",
  },
  infoValue: {
    fontSize: 14,
    color: "#333",
  },
  statsSection: {
    marginBottom: 20,
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  statCard: {
    width: "48%",
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 15,
    marginBottom: 12,
    alignItems: "center",
    borderColor: "#e0e0e0",
    borderWidth: 1,
  },
  statLabel: {
    fontSize: 12,
    color: "#666",
    marginBottom: 8,
    fontWeight: "600",
  },
  statValue: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#007bff",
  },
  actionsSection: {
    gap: 10,
    marginBottom: 20,
  },
  completeButton: {
    backgroundColor: "#28a745",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  completeButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  editButton: {
    backgroundColor: "#007bff",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  editButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  deleteButton: {
    backgroundColor: "#dc3545",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  deleteButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  editSection: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 15,
    borderColor: "#e0e0e0",
    borderWidth: 1,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    borderColor: "#ddd",
    borderWidth: 1,
    borderRadius: 6,
    padding: 10,
    fontSize: 14,
    color: "#333",
    backgroundColor: "#fafafa",
  },
  frequencyContainer: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 15,
  },
  frequencyButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderColor: "#ddd",
    borderWidth: 1,
    alignItems: "center",
    backgroundColor: "#fff",
  },
  frequencyButtonActive: {
    backgroundColor: "#007bff",
    borderColor: "#007bff",
  },
  frequencyButtonText: {
    fontSize: 14,
    color: "#666",
    fontWeight: "500",
  },
  frequencyButtonTextActive: {
    color: "#fff",
  },
  saveButton: {
    backgroundColor: "#28a745",
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 15,
  },
  saveButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  cancelButton: {
    backgroundColor: "#6c757d",
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 10,
  },
  cancelButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  errorText: {
    color: "#dc3545",
    fontSize: 16,
    textAlign: "center",
    marginTop: 20,
  },
});
