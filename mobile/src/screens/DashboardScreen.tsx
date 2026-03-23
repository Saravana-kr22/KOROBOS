/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Dashboard screen for mobile (React Native).
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { LineChart } from "react-native-chart-kit";
import { useFocusEffect } from "@react-navigation/native";
import { useRouter } from "expo-router";
import { analyticsApi, AnalyticsOverview } from "../services/analyticsApi";
import { getSummary } from "../api/aiApi";

const DashboardScreen = () => {
  const router = useRouter();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      const [overviewData, summaryData] = await Promise.all([
        analyticsApi.getOverview(),
        getSummary().catch(() => null),
      ]);
      setOverview(overviewData);
      if (summaryData) {
        setSummary(summaryData.summary);
      }
      setIsStale(false);

      // Cache to AsyncStorage on success
      try {
        await AsyncStorage.setItem(
          "korobos:dashboard_cache",
          JSON.stringify({ overview: overviewData }),
        );
      } catch (cacheErr) {
        console.warn("Failed to cache dashboard data:", cacheErr);
      }
    } catch (err) {
      console.warn("Failed to load dashboard:", err);
      // Try to load from cache on error
      try {
        const cached = await AsyncStorage.getItem("korobos:dashboard_cache");
        if (cached) {
          const { overview: cachedOverview } = JSON.parse(cached);
          setOverview(cachedOverview);
          setIsStale(true);
        }
      } catch (cacheErr) {
        console.warn("Failed to load cached dashboard data:", cacheErr);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadDashboard();
    }, [loadDashboard]),
  );

  const getScoreColor = (score: number) => {
    if (score < 40) return "#dc3545";
    if (score < 70) return "#ffc107";
    return "#28a745";
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={loadDashboard} />
      }
    >
      {/* Offline/Stale Data Banner */}
      {isStale && (
        <View style={styles.staleBanner}>
          <Text style={styles.staleBannerText}>
            📡 Showing cached data (offline mode)
          </Text>
        </View>
      )}

      {/* Insight Highlights Card */}
      {summary && (
        <TouchableOpacity
          style={styles.insightCard}
          onPress={() => router.push("/ai/insights")}
          activeOpacity={0.7}
        >
          <Text style={styles.insightCardIcon}>🧠</Text>
          <View style={styles.insightCardContent}>
            <Text style={styles.insightCardTitle}>AI Insight Highlight</Text>
            <Text style={styles.insightCardText} numberOfLines={2}>
              {summary}
            </Text>
            <Text style={styles.insightCardCTA}>View all insights →</Text>
          </View>
        </TouchableOpacity>
      )}

      {/* Overview Card */}
      {overview && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Productivity Overview</Text>
          <View style={styles.overviewGrid}>
            <View style={styles.metricBox}>
              <Text
                style={[
                  styles.metricValue,
                  { color: getScoreColor(overview.productivity_score) },
                ]}
              >
                {overview.productivity_score}
              </Text>
              <Text style={styles.metricLabel}>Score</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {overview.habits.completion_rate.toFixed(0)}%
              </Text>
              <Text style={styles.metricLabel}>Habits</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {(overview.learning.learning_hours * 60).toFixed(0)}
              </Text>
              <Text style={styles.metricLabel}>Learning (min)</Text>
            </View>
            <View style={styles.metricBox}>
              <Text
                style={[
                  styles.metricValue,
                  {
                    color: overview.health.balance > 0 ? "#dc3545" : "#28a745",
                  },
                ]}
              >
                {Math.round(overview.health.balance)}
              </Text>
              <Text style={styles.metricLabel}>Cal Balance</Text>
            </View>
          </View>
          <View style={styles.additionalMetrics}>
            <Text style={styles.additionalLabel}>
              Streak:{" "}
              <Text style={{ fontWeight: "600" }}>
                {overview.habits.current_streak}
              </Text>{" "}
              days
            </Text>
            <Text style={styles.additionalLabel}>
              Health:{" "}
              <Text style={{ fontWeight: "600" }}>
                {Math.round(overview.health.intake)} kcal
              </Text>
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    padding: 16,
  },
  staleBanner: {
    backgroundColor: "#fff3cd",
    borderWidth: 1,
    borderColor: "#ffeaa7",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  staleBannerText: {
    color: "#856404",
    fontSize: 13,
    fontWeight: "500",
  },
  insightCard: {
    flexDirection: "row",
    backgroundColor: "#f0f4ff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: "#3b82f6",
    alignItems: "flex-start",
  },
  insightCardIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  insightCardContent: {
    flex: 1,
  },
  insightCardTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1e40af",
    marginBottom: 4,
  },
  insightCardText: {
    fontSize: 13,
    lineHeight: 18,
    color: "#333",
    marginBottom: 8,
  },
  insightCardCTA: {
    fontSize: 12,
    fontWeight: "600",
    color: "#3b82f6",
  },
  card: {
    backgroundColor: "#f8f9fa",
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#dee2e6",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 12,
  },
  overviewGrid: {
    display: "flex",
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  metricBox: {
    width: "48%",
    alignItems: "center",
    marginBottom: 16,
  },
  metricValue: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: "#666",
  },
  dayItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  dayDate: {
    fontSize: 12,
    color: "#666",
    minWidth: 80,
  },
  dayStats: {
    flex: 1,
    height: 8,
    backgroundColor: "#e0e0e0",
    borderRadius: 4,
    marginHorizontal: 10,
    overflow: "hidden",
  },
  scoreBar: {
    height: 8,
    borderRadius: 4,
  },
  dayScore: {
    fontSize: 12,
    fontWeight: "600",
    minWidth: 50,
    textAlign: "right",
  },
  additionalMetrics: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#dee2e6",
  },
  additionalLabel: {
    fontSize: 13,
    color: "#666",
    marginVertical: 4,
  },
});

export default DashboardScreen;
