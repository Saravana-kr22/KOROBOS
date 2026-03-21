"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

interface HealthLog {
  id: string;
  user_id: string;
  log_type: string;
  calories: number | null;
  duration: number | null;
  description: string | null;
  food_name: string | null;
  workout_type: string | null;
  protein: number | null;
  carbs: number | null;
  fat: number | null;
  created_at: string;
  updated_at: string;
}

interface DailyStats {
  calories_consumed: number;
  calories_burned: number;
  net_calories: number;
}

export default function HealthPage() {
  const [dailyStats, setDailyStats] = useState<DailyStats | null>(null);
  const [logs, setLogs] = useState<HealthLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"meals" | "workouts">("meals");
  const [mealForm, setMealForm] = useState({
    food_name: "",
    calories: "",
    protein: "",
    carbs: "",
    fat: "",
    description: "",
  });
  const [workoutForm, setWorkoutForm] = useState({
    workout_type: "",
    duration: "",
    calories: "",
    description: "",
  });
  const [error, setError] = useState("");
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const loadHealth = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Load daily stats
      const statsRes = await fetch("/api/v1/health/daily", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (statsRes.ok) {
        const data = await statsRes.json();
        setDailyStats(data);
      }

      // Load recent logs
      const logsRes = await fetch("/api/v1/health/logs?limit=20", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(data.logs || []);
      }
    } catch {
      setError("Failed to load health data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    loadHealth();
  }, [token, loadHealth]);

  const handleLogMeal = async (e: FormEvent) => {
    e.preventDefault();
    if (!mealForm.calories.trim()) {
      setError("Calories is required");
      return;
    }

    try {
      const res = await fetch("/api/v1/health/meals", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          calories: parseInt(mealForm.calories),
          food_name: mealForm.food_name || undefined,
          protein: mealForm.protein ? parseInt(mealForm.protein) : undefined,
          carbs: mealForm.carbs ? parseInt(mealForm.carbs) : undefined,
          fat: mealForm.fat ? parseInt(mealForm.fat) : undefined,
          description: mealForm.description || undefined,
        }),
      });

      if (res.ok) {
        setMealForm({
          food_name: "",
          calories: "",
          protein: "",
          carbs: "",
          fat: "",
          description: "",
        });
        await loadHealth();
      } else {
        setError("Failed to log meal");
      }
    } catch {
      setError("Failed to log meal");
    }
  };

  const handleLogWorkout = async (e: FormEvent) => {
    e.preventDefault();
    if (!workoutForm.duration.trim()) {
      setError("Duration is required");
      return;
    }

    try {
      const res = await fetch("/api/v1/health/workouts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          duration: parseInt(workoutForm.duration),
          workout_type: workoutForm.workout_type || undefined,
          calories: workoutForm.calories
            ? parseInt(workoutForm.calories)
            : undefined,
          description: workoutForm.description || undefined,
        }),
      });

      if (res.ok) {
        setWorkoutForm({
          workout_type: "",
          duration: "",
          calories: "",
          description: "",
        });
        await loadHealth();
      } else {
        setError("Failed to log workout");
      }
    } catch {
      setError("Failed to log workout");
    }
  };

  const deleteLog = async (logId: string) => {
    try {
      const res = await fetch(`/api/v1/health/logs/${logId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        await loadHealth();
      }
    } catch {
      setError("Failed to delete log");
    }
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "20px" }}>
      <h1>Health Tracking</h1>

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

      {/* Daily Summary */}
      {dailyStats && (
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "20px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid #dee2e6",
          }}
        >
          <h2>Today&apos;s Summary</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: "20px",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "24px", fontWeight: "bold" }}>
                {dailyStats.calories_consumed}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Consumed (kcal)
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "24px", fontWeight: "bold" }}>
                {dailyStats.calories_burned}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>
                Burned (kcal)
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: dailyStats.net_calories > 0 ? "#dc3545" : "#28a745",
                }}
              >
                {dailyStats.net_calories}
              </div>
              <div style={{ color: "#666", fontSize: "14px" }}>Net (kcal)</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={() => setActiveTab("meals")}
          style={{
            padding: "10px 20px",
            marginRight: "10px",
            backgroundColor: activeTab === "meals" ? "#007bff" : "#f0f0f0",
            color: activeTab === "meals" ? "white" : "#333",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Log Meal
        </button>
        <button
          onClick={() => setActiveTab("workouts")}
          style={{
            padding: "10px 20px",
            backgroundColor: activeTab === "workouts" ? "#007bff" : "#f0f0f0",
            color: activeTab === "workouts" ? "white" : "#333",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Log Workout
        </button>
      </div>

      {/* Meal Form */}
      {activeTab === "meals" && (
        <form
          onSubmit={handleLogMeal}
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "8px",
            marginBottom: "20px",
          }}
        >
          <h3>Log Meal</h3>
          <input
            type="text"
            placeholder="Food name (optional)"
            value={mealForm.food_name}
            onChange={(e) =>
              setMealForm({ ...mealForm, food_name: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <input
            type="number"
            placeholder="Calories (required)"
            value={mealForm.calories}
            onChange={(e) =>
              setMealForm({ ...mealForm, calories: e.target.value })
            }
            required
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: "10px",
            }}
          >
            <input
              type="number"
              placeholder="Protein (g)"
              value={mealForm.protein}
              onChange={(e) =>
                setMealForm({ ...mealForm, protein: e.target.value })
              }
              style={{
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            />
            <input
              type="number"
              placeholder="Carbs (g)"
              value={mealForm.carbs}
              onChange={(e) =>
                setMealForm({ ...mealForm, carbs: e.target.value })
              }
              style={{
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            />
            <input
              type="number"
              placeholder="Fat (g)"
              value={mealForm.fat}
              onChange={(e) =>
                setMealForm({ ...mealForm, fat: e.target.value })
              }
              style={{
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            />
          </div>
          <textarea
            placeholder="Notes (optional)"
            value={mealForm.description}
            onChange={(e) =>
              setMealForm({ ...mealForm, description: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginTop: "10px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
              minHeight: "60px",
            }}
          />
          <button
            type="submit"
            style={{
              padding: "8px 16px",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Log Meal
          </button>
        </form>
      )}

      {/* Workout Form */}
      {activeTab === "workouts" && (
        <form
          onSubmit={handleLogWorkout}
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "8px",
            marginBottom: "20px",
          }}
        >
          <h3>Log Workout</h3>
          <input
            type="text"
            placeholder="Workout type (e.g., Running, Swimming)"
            value={workoutForm.workout_type}
            onChange={(e) =>
              setWorkoutForm({ ...workoutForm, workout_type: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <input
            type="number"
            placeholder="Duration (minutes, required)"
            value={workoutForm.duration}
            onChange={(e) =>
              setWorkoutForm({ ...workoutForm, duration: e.target.value })
            }
            required
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <input
            type="number"
            placeholder="Calories burned (optional)"
            value={workoutForm.calories}
            onChange={(e) =>
              setWorkoutForm({ ...workoutForm, calories: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <textarea
            placeholder="Notes (optional)"
            value={workoutForm.description}
            onChange={(e) =>
              setWorkoutForm({ ...workoutForm, description: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
              minHeight: "60px",
            }}
          />
          <button
            type="submit"
            style={{
              padding: "8px 16px",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Log Workout
          </button>
        </form>
      )}

      {/* Recent Logs */}
      <section>
        <h2>Recent Logs ({logs.length})</h2>
        {logs.length === 0 ? (
          <p style={{ color: "#666" }}>No logs yet</p>
        ) : (
          <div>
            {logs.map((log) => (
              <div
                key={log.id}
                style={{
                  padding: "12px",
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  marginBottom: "8px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  backgroundColor:
                    log.log_type === "meal" ? "#f0f8ff" : "#f0fff0",
                }}
              >
                <div style={{ flex: 1 }}>
                  <strong>
                    {log.log_type === "meal"
                      ? `🍽️ ${log.food_name || "Meal"}`
                      : `💪 ${log.workout_type || "Workout"}`}
                  </strong>
                  <div
                    style={{
                      fontSize: "14px",
                      color: "#666",
                      marginTop: "4px",
                    }}
                  >
                    {log.log_type === "meal"
                      ? `${log.calories} kcal ${
                          log.protein || log.carbs || log.fat
                            ? `(P: ${log.protein}g C: ${log.carbs}g F: ${log.fat}g)`
                            : ""
                        }`
                      : `${log.duration} min ${
                          log.calories ? `(${log.calories} kcal)` : ""
                        }`}
                  </div>
                  {log.description && (
                    <div
                      style={{
                        fontSize: "13px",
                        color: "#999",
                        marginTop: "2px",
                      }}
                    >
                      {log.description}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => deleteLog(log.id)}
                  style={{
                    padding: "6px 12px",
                    backgroundColor: "#dc3545",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
