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
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { LineChart } from "react-native-chart-kit";
import { useFocusEffect } from "@react-navigation/native";
import { dashboardApi } from "../services/dashboardApi";
import {
  DailyMetrics,
  OverviewResponse,
  WeeklyResponse,
} from "../types/dashboard";

const DashboardScreen = () => {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      const [overviewData, weeklyData] = await Promise.all([
        dashboardApi.getOverview(),
        dashboardApi.getWeekly(),
      ]);
      setOverview(overviewData);
      setWeekly(weeklyData);
      setIsStale(false);

      // Cache to AsyncStorage on success
      try {
        await AsyncStorage.setItem(
          "korobos:dashboard_cache",
          JSON.stringify({ overview: overviewData, weekly: weeklyData }),
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
          const { overview: cachedOverview, weekly: cachedWeekly } =
            JSON.parse(cached);
          setOverview(cachedOverview);
          setWeekly(cachedWeekly);
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

      {/* Overview Card */}
      {overview && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Today's Summary</Text>
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
              <Text style={styles.metricLabel}>Productivity Score</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {overview.habits_completed}
              </Text>
              <Text style={styles.metricLabel}>Habits</Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {overview.learning_minutes}
              </Text>
              <Text style={styles.metricLabel}>Learning (min)</Text>
            </View>
            <View style={styles.metricBox}>
              <Text
                style={[
                  styles.metricValue,
                  {
                    color:
                      overview.calories_balance > 0 ? "#dc3545" : "#28a745",
                  },
                ]}
              >
                {overview.calories_balance}
              </Text>
              <Text style={styles.metricLabel}>Cal Balance</Text>
            </View>
          </View>
        </View>
      )}

      {/* Weekly Section */}
      {weekly && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Weekly Trends</Text>
          <LineChart
            data={{
              labels: weekly.days.map((day) => day.date.slice(5)), // MM-DD format
              datasets: [
                {
                  data: weekly.days.map((day) => day.productivity_score),
                  color: (opacity = 1) => `rgba(0, 123, 255, ${opacity})`, // #007bff
                  strokeWidth: 2,
                },
              ],
            }}
            width={Dimensions.get("window").width - 48}
            height={220}
            yAxisLabel=""
            yAxisSuffix=""
            yMin={0}
            yMax={100}
            chartConfig={{
              backgroundColor: "#f8f9fa",
              backgroundGradientFrom: "#f8f9fa",
              backgroundGradientTo: "#f8f9fa",
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: { borderRadius: 8 },
              propsForDots: {
                r: "4",
                strokeWidth: "2",
                stroke: "#007bff",
              },
            }}
            bezier
            style={{ marginVertical: 16, borderRadius: 8 }}
          />
          <View style={styles.weeklyStats}>
            <Text style={styles.weeklyStatText}>
              Avg Score:{" "}
              <Text style={{ fontWeight: "600" }}>
                {weekly.avg_productivity_score}
              </Text>
            </Text>
            <Text style={styles.weeklyStatText}>
              Total Learning:{" "}
              <Text style={{ fontWeight: "600" }}>
                {weekly.total_learning_minutes} min
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
  weeklyStats: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#dee2e6",
  },
  weeklyStatText: {
    fontSize: 13,
    color: "#666",
    marginVertical: 4,
  },
});

export default DashboardScreen;
