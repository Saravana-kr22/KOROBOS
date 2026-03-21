"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

interface DailyMetrics {
  date: string;
  habits_completed: number;
  total_habits: number;
  learning_minutes: number;
  calories_consumed: number;
  calories_burned: number;
  net_calories: number;
  productivity_score: number;
}

interface WeeklyResponse {
  week_start: string;
  week_end: string;
  days: DailyMetrics[];
  avg_productivity_score: number;
  total_learning_minutes: number;
  avg_habits_completed: number;
}

interface OverviewResponse {
  date: string;
  habits_completed: number;
  learning_minutes: number;
  calories_balance: number;
  productivity_score: number;
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Load overview
      const overviewRes = await fetch("/api/v1/dashboard/overview", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (overviewRes.ok) {
        const data = await overviewRes.json();
        setOverview(data);
      }

      // Load weekly
      const weeklyRes = await fetch("/api/v1/dashboard/weekly", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (weeklyRes.ok) {
        const data = await weeklyRes.json();
        setWeekly(data);
      }
    } catch (_err) {
      setError("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    loadDashboard();
  }, [token, loadDashboard]);

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  const scoreColor =
    overview && overview.productivity_score < 40
      ? "#dc3545"
      : overview && overview.productivity_score < 70
      ? "#ffc107"
      : "#28a745";

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px" }}>
      <h1>Dashboard</h1>

      {error && (
        <div
          style={{
            backgroundColor: "#ffe0e0",
            color: "#d00",
            padding: "10px",
            borderRadius: "4px",
            marginBottom: "20px",
          }}
        >
          {error}
        </div>
      )}

      {/* Summary Card */}
      {overview && (
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "20px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid #dee2e6",
          }}
        >
          <h2>Today's Summary</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr 1fr",
              gap: "20px",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "48px",
                  fontWeight: "bold",
                  color: scoreColor,
                }}
              >
                {overview.productivity_score}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Productivity Score
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "32px", fontWeight: "bold" }}>
                {overview.habits_completed}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Habits Completed
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "32px", fontWeight: "bold" }}>
                {overview.learning_minutes}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Learning Minutes
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "32px",
                  fontWeight: "bold",
                  color: overview.calories_balance > 0 ? "#dc3545" : "#28a745",
                }}
              >
                {overview.calories_balance}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Calories Balance
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Weekly Trends */}
      {weekly && (
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "20px",
            borderRadius: "8px",
            border: "1px solid #dee2e6",
          }}
        >
          <h2>Weekly Trends</h2>
          <p style={{ color: "#666", marginBottom: "15px" }}>
            {weekly.week_start} to {weekly.week_end}
          </p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #dee2e6" }}>
                  <th style={{ textAlign: "left", padding: "10px" }}>Date</th>
                  <th style={{ textAlign: "center", padding: "10px" }}>
                    Score
                  </th>
                  <th style={{ textAlign: "center", padding: "10px" }}>
                    Habits
                  </th>
                  <th style={{ textAlign: "center", padding: "10px" }}>
                    Learning (min)
                  </th>
                </tr>
              </thead>
              <tbody>
                {weekly.days.map((day) => (
                  <tr key={day.date} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "10px" }}>{day.date}</td>
                    <td style={{ textAlign: "center", padding: "10px" }}>
                      <div
                        style={{
                          display: "inline-block",
                          backgroundColor:
                            day.productivity_score < 40
                              ? "#ffe0e0"
                              : day.productivity_score < 70
                              ? "#fff3cd"
                              : "#d4edda",
                          padding: "5px 10px",
                          borderRadius: "4px",
                          fontWeight: "bold",
                        }}
                      >
                        {day.productivity_score}
                      </div>
                    </td>
                    <td style={{ textAlign: "center", padding: "10px" }}>
                      {day.habits_completed}/{day.total_habits}
                    </td>
                    <td style={{ textAlign: "center", padding: "10px" }}>
                      {day.learning_minutes}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div
            style={{
              marginTop: "15px",
              paddingTop: "15px",
              borderTop: "1px solid #dee2e6",
            }}
          >
            <p style={{ margin: "5px 0", color: "#666" }}>
              <strong>Weekly Averages:</strong>
            </p>
            <p style={{ margin: "5px 0", color: "#666" }}>
              Productivity Score:{" "}
              <strong>{weekly.avg_productivity_score}</strong>
            </p>
            <p style={{ margin: "5px 0", color: "#666" }}>
              Learning Minutes: <strong>{weekly.total_learning_minutes}</strong>
            </p>
            <p style={{ margin: "5px 0", color: "#666" }}>
              Habits/Day: <strong>{weekly.avg_habits_completed}</strong>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
