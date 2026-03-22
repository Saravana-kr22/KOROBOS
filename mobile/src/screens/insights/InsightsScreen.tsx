/*
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Insights Screen — displays AI-generated insights about user behavior.
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
import { getInsights, Insight } from "../../api/aiApi";

const INSIGHT_COLORS = {
  behavioral: "#3b82f6",
  performance: "#10b981",
  health: "#f59e0b",
  knowledge: "#8b5cf6",
};

const INSIGHT_ICONS = {
  behavioral: "📊",
  performance: "📈",
  health: "❤️",
  knowledge: "🧠",
};

export const InsightsScreen: React.FC = () => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadInsights = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getInsights(selectedType || undefined, 20);
      setInsights(data.insights);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load insights");
    } finally {
      setLoading(false);
    }
  }, [selectedType]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadInsights();
    setRefreshing(false);
  }, [loadInsights]);

  useEffect(() => {
    loadInsights();
  }, [selectedType]);

  const renderInsight = ({ item }: { item: Insight }) => (
    <View
      style={[
        styles.insightCard,
        { borderLeftColor: INSIGHT_COLORS[item.insight_type] },
      ]}
    >
      <View style={styles.insightHeader}>
        <Text style={styles.insightIcon}>
          {INSIGHT_ICONS[item.insight_type]}
        </Text>
        <View style={styles.insightTypeContainer}>
          <Text style={styles.insightType}>{item.insight_type}</Text>
          <Text style={styles.insightConfidence}>
            Confidence: {(item.confidence * 100).toFixed(0)}%
          </Text>
        </View>
      </View>
      <Text style={styles.insightText}>{item.text}</Text>
      <Text style={styles.insightDate}>
        {new Date(item.created_at).toLocaleDateString()}
      </Text>
    </View>
  );

  const filterButtons = [
    { label: "All", value: null },
    { label: "Behavioral", value: "behavioral" },
    { label: "Performance", value: "performance" },
    { label: "Health", value: "health" },
    { label: "Knowledge", value: "knowledge" },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Your Insights</Text>
        <Text style={styles.subtitle}>
          AI-powered analysis of your behavior and progress
        </Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterScroll}
        contentContainerStyle={styles.filterContainer}
      >
        {filterButtons.map((btn) => (
          <TouchableOpacity
            key={btn.value || "all"}
            style={[
              styles.filterButton,
              selectedType === btn.value && styles.filterButtonActive,
            ]}
            onPress={() => setSelectedType(btn.value)}
          >
            <Text
              style={[
                styles.filterButtonText,
                selectedType === btn.value && styles.filterButtonTextActive,
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
          <TouchableOpacity style={styles.retryButton} onPress={loadInsights}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {loading && !refreshing ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.loadingText}>Loading insights...</Text>
        </View>
      ) : insights.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyText}>No insights yet</Text>
          <Text style={styles.emptySubText}>
            Keep tracking your activities for personalized insights
          </Text>
        </View>
      ) : (
        <FlatList
          data={insights}
          renderItem={renderInsight}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}
    </SafeAreaView>
  );
};

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
  insightCard: {
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
  insightHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  insightIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  insightTypeContainer: {
    flex: 1,
  },
  insightType: {
    fontSize: 13,
    fontWeight: "600",
    textTransform: "capitalize",
    color: "#374151",
    marginBottom: 2,
  },
  insightConfidence: {
    fontSize: 12,
    color: "#9ca3af",
  },
  insightText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#111827",
    marginBottom: 12,
  },
  insightDate: {
    fontSize: 12,
    color: "#9ca3af",
  },
});
