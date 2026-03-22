/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Recommendations Screen — displays actionable AI recommendations.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { getRecommendations } from "../src/api/aiApi";

const CATEGORY_COLORS = {
  habit: "#f59e0b",
  learning: "#10b981",
  health: "#ef4444",
  productivity: "#3b82f6",
};

const CATEGORY_ICONS = {
  habit: "✅",
  learning: "📚",
  health: "🥗",
  productivity: "⚡",
};

const PRIORITY_COLORS = {
  high: "#dc2626",
  medium: "#f59e0b",
  low: "#6b7280",
};

const PRIORITY_LABELS = {
  high: "🔴 High",
  medium: "🟡 Medium",
  low: "⚫ Low",
};

interface Recommendation {
  id: string;
  user_id: string;
  category: "habit" | "learning" | "health" | "productivity";
  text: string;
  priority: "high" | "medium" | "low";
  metadata_json?: Record<string, any>;
  created_at: string;
}

export default function RecommendationsScreen() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getRecommendations(selectedCategory || undefined, 20);
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load recommendations",
      );
    } finally {
      setLoading(false);
    }
  }, [selectedCategory]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadRecommendations();
    setRefreshing(false);
  }, [loadRecommendations]);

  useEffect(() => {
    loadRecommendations();
  }, [selectedCategory]);

  const renderRecommendation = ({ item }: { item: Recommendation }) => (
    <View
      style={[
        styles.recCard,
        { borderLeftColor: CATEGORY_COLORS[item.category] },
      ]}
    >
      <View style={styles.recHeader}>
        <Text style={styles.recIcon}>{CATEGORY_ICONS[item.category]}</Text>
        <View style={styles.recHeaderText}>
          <View style={styles.recTitleRow}>
            <Text style={styles.recCategory}>{item.category}</Text>
            <View
              style={[
                styles.priorityBadge,
                { backgroundColor: PRIORITY_COLORS[item.priority] },
              ]}
            >
              <Text style={styles.priorityLabel}>
                {PRIORITY_LABELS[item.priority]}
              </Text>
            </View>
          </View>
        </View>
      </View>
      <Text style={styles.recText}>{item.text}</Text>
      <Text style={styles.recDate}>
        {new Date(item.created_at).toLocaleDateString()}
      </Text>
    </View>
  );

  const categoryButtons = [
    { label: "All", value: null },
    { label: "Habit", value: "habit" },
    { label: "Learning", value: "learning" },
    { label: "Health", value: "health" },
    { label: "Productivity", value: "productivity" },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Recommendations</Text>
        <Text style={styles.subtitle}>
          Actionable suggestions to improve your performance
        </Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterScroll}
        contentContainerStyle={styles.filterContainer}
      >
        {categoryButtons.map((btn) => (
          <TouchableOpacity
            key={btn.value || "all"}
            style={[
              styles.filterButton,
              selectedCategory === btn.value && styles.filterButtonActive,
            ]}
            onPress={() => setSelectedCategory(btn.value)}
          >
            <Text
              style={[
                styles.filterButtonText,
                selectedCategory === btn.value && styles.filterButtonTextActive,
              ]}
            >
              {btn.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadRecommendations}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {loading && !refreshing ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.loadingText}>Loading recommendations...</Text>
        </View>
      ) : recommendations.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyText}>No recommendations yet</Text>
          <Text style={styles.emptySubText}>
            Start logging activities to get personalized recommendations
          </Text>
        </View>
      ) : (
        <FlatList
          data={recommendations}
          renderItem={renderRecommendation}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9fafb",
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#6b7280",
  },
  filterScroll: {
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },
  filterContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "#f3f4f6",
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  filterButtonActive: {
    backgroundColor: "#3b82f6",
    borderColor: "#3b82f6",
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#6b7280",
  },
  filterButtonTextActive: {
    color: "#fff",
  },
  errorContainer: {
    marginHorizontal: 16,
    marginTop: 16,
    padding: 12,
    backgroundColor: "#fee2e2",
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: "#dc2626",
  },
  errorText: {
    fontSize: 14,
    color: "#991b1b",
    marginBottom: 8,
  },
  retryButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#dc2626",
    borderRadius: 4,
    alignSelf: "flex-start",
  },
  retryButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 13,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 16,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: "#6b7280",
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 8,
  },
  emptySubText: {
    fontSize: 14,
    color: "#6b7280",
    textAlign: "center",
  },
  listContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  recCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    marginBottom: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  recHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  recIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  recHeaderText: {
    flex: 1,
  },
  recTitleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  recCategory: {
    fontSize: 13,
    fontWeight: "600",
    textTransform: "capitalize",
    color: "#374151",
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  priorityLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#fff",
  },
  recText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#111827",
    marginBottom: 12,
  },
  recDate: {
    fontSize: 12,
    color: "#9ca3af",
  },
});
