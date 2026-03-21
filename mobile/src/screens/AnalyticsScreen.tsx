/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Analytics screen for detailed metrics (React Native).
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { LineChart } from "react-native-chart-kit";
import { useFocusEffect } from "@react-navigation/native";
import {
  analyticsApi,
  AnalyticsOverview,
  AllTrends,
} from "../services/analyticsApi";

const AnalyticsScreen = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AllTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);

  const loadAnalytics = useCallback(async () => {
    try {
      const [overviewData, trendsData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getTrends("7d"),
      ]);
      setOverview(overviewData);
      setTrends(trendsData);
      setIsStale(false);

      // Cache to AsyncStorage on success
      try {
        await AsyncStorage.setItem(
          "korobos:analytics_cache",
          JSON.stringify({ overview: overviewData, trends: trendsData }),
        );
      } catch (cacheErr) {
        console.warn("Failed to cache analytics data:", cacheErr);
      }
    } catch (err) {
      console.warn("Failed to load analytics:", err);
      // Try to load from cache on error
      try {
        const cached = await AsyncStorage.getItem("korobos:analytics_cache");
        if (cached) {
          const { overview: cachedOverview, trends: cachedTrends } =
            JSON.parse(cached);
          setOverview(cachedOverview);
          setTrends(cachedTrends);
          setIsStale(true);
        }
      } catch (cacheErr) {
        console.warn("Failed to load cached analytics data:", cacheErr);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadAnalytics();
    }, [loadAnalytics]),
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
        <RefreshControl refreshing={refreshing} onRefresh={loadAnalytics} />
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

      {/* Productivity Overview */}
      {overview && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Productivity Overview</Text>
          <View style={styles.scoreCard}>
            <Text
              style={[
                styles.largeScore,
                { color: getScoreColor(overview.productivity_score) },
              ]}
            >
              {overview.productivity_score}
            </Text>
            <Text style={styles.scoreLabel}>Overall Score</Text>
          </View>
        </View>
      )}

      {/* Domain Metrics */}
      {overview && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Domain Metrics</Text>

          {/* Habits */}
          <View style={styles.metricSection}>
            <Text style={styles.sectionTitle}>📅 Habits</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Completion Rate:</Text>
              <Text style={styles.metricValue}>
                {overview.habits.completion_rate.toFixed(1)}%
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Current Streak:</Text>
              <Text style={styles.metricValue}>
                {overview.habits.current_streak} days
              </Text>
            </View>
          </View>

          {/* Learning */}
          <View style={styles.metricSection}>
            <Text style={styles.sectionTitle}>📚 Learning</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Daily Hours:</Text>
              <Text style={styles.metricValue}>
                {overview.learning.learning_hours.toFixed(2)} hrs
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Consistency:</Text>
              <Text style={styles.metricValue}>
                {overview.learning.habit_consistency.toFixed(1)}%
              </Text>
            </View>
          </View>

          {/* Health */}
          <View style={styles.metricSection}>
            <Text style={styles.sectionTitle}>🏃 Health</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Intake:</Text>
              <Text style={styles.metricValue}>
                {Math.round(overview.health.intake)} kcal
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Burned:</Text>
              <Text style={styles.metricValue}>
                {Math.round(overview.health.burned)} kcal
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Balance:</Text>
              <Text
                style={[
                  styles.metricValue,
                  {
                    color: overview.health.balance > 0 ? "#dc3545" : "#28a745",
                  },
                ]}
              >
                {Math.round(overview.health.balance)} kcal
              </Text>
            </View>
          </View>

          {/* Knowledge */}
          <View style={styles.metricSection}>
            <Text style={styles.sectionTitle}>📝 Knowledge</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Notes Created:</Text>
              <Text style={styles.metricValue}>
                {overview.knowledge.notes_created.toFixed(1)}
              </Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Records Created:</Text>
              <Text style={styles.metricValue}>
                {overview.knowledge.records_created.toFixed(1)}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* 7-Day Trends */}
      {trends && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>7-Day Trends</Text>

          {/* Habit Completion Trend */}
          {trends.habits && trends.habits.values.length > 0 && (
            <View style={styles.trendSection}>
              <Text style={styles.trendTitle}>Habit Completion Rate</Text>
              <LineChart
                data={{
                  labels: trends.habits.labels.map((label) => label.slice(5)), // MM-DD format
                  datasets: [
                    {
                      data: trends.habits.values,
                      color: (opacity = 1) => `rgba(40, 167, 69, ${opacity})`,
                      strokeWidth: 2,
                    },
                  ],
                }}
                width={Dimensions.get("window").width - 48}
                height={200}
                chartConfig={{
                  backgroundColor: "#f8f9fa",
                  backgroundGradientFrom: "#f8f9fa",
                  backgroundGradientTo: "#f8f9fa",
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: { borderRadius: 8 },
                  propsForDots: {
                    r: "3",
                    strokeWidth: "2",
                    stroke: "#28a745",
                  },
                }}
                yAxisLabel=""
                yAxisSuffix="%"
                fromZero={true}
                bezier
                style={{ marginVertical: 16, borderRadius: 8 }}
              />
            </View>
          )}

          {/* Learning Hours Trend */}
          {trends.learning && trends.learning.values.length > 0 && (
            <View style={styles.trendSection}>
              <Text style={styles.trendTitle}>Learning Hours</Text>
              <LineChart
                data={{
                  labels: trends.learning.labels.map((label) => label.slice(5)), // MM-DD format
                  datasets: [
                    {
                      data: trends.learning.values,
                      color: (opacity = 1) => `rgba(0, 123, 255, ${opacity})`,
                      strokeWidth: 2,
                    },
                  ],
                }}
                width={Dimensions.get("window").width - 48}
                height={200}
                chartConfig={{
                  backgroundColor: "#f8f9fa",
                  backgroundGradientFrom: "#f8f9fa",
                  backgroundGradientTo: "#f8f9fa",
                  decimalPlaces: 1,
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: { borderRadius: 8 },
                  propsForDots: {
                    r: "3",
                    strokeWidth: "2",
                    stroke: "#007bff",
                  },
                }}
                yAxisLabel=""
                yAxisSuffix="h"
                fromZero={true}
                bezier
                style={{ marginVertical: 16, borderRadius: 8 }}
              />
            </View>
          )}

          {/* Calorie Balance Trend */}
          {trends.health_intake && trends.health_intake.values.length > 0 && (
            <View style={styles.trendSection}>
              <Text style={styles.trendTitle}>Calorie Balance</Text>
              <LineChart
                data={{
                  labels: trends.health_intake.labels.map((label) =>
                    label.slice(5),
                  ), // MM-DD format
                  datasets: [
                    {
                      data: trends.health_intake.values.map((intake, idx) =>
                        Math.round(intake - trends.health_burned.values[idx]),
                      ),
                      color: (opacity = 1) => `rgba(220, 53, 69, ${opacity})`,
                      strokeWidth: 2,
                    },
                  ],
                }}
                width={Dimensions.get("window").width - 48}
                height={200}
                chartConfig={{
                  backgroundColor: "#f8f9fa",
                  backgroundGradientFrom: "#f8f9fa",
                  backgroundGradientTo: "#f8f9fa",
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: { borderRadius: 8 },
                  propsForDots: {
                    r: "3",
                    strokeWidth: "2",
                    stroke: "#dc3545",
                  },
                }}
                yAxisLabel=""
                yAxisSuffix="kcal"
                fromZero={true}
                bezier
                style={{ marginVertical: 16, borderRadius: 8 }}
              />
            </View>
          )}
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
    marginBottom: 16,
  },
  scoreCard: {
    alignItems: "center",
    paddingVertical: 20,
  },
  largeScore: {
    fontSize: 48,
    fontWeight: "bold",
    marginBottom: 8,
  },
  scoreLabel: {
    fontSize: 14,
    color: "#666",
  },
  metricSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#dee2e6",
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 12,
    color: "#333",
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 13,
    color: "#666",
    flex: 1,
  },
  metricValue: {
    fontSize: 13,
    fontWeight: "600",
    color: "#007bff",
  },
  trendSection: {
    marginBottom: 24,
  },
  trendTitle: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 12,
    color: "#333",
  },
});

export default AnalyticsScreen;
