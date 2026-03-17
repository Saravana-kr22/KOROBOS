"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

interface Habit {
  id: string;
  user_id: string;
  name: string;
  frequency: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface HabitStats {
  habit_id: string;
  completion_rate: number;
  current_streak: number;
  longest_streak: number;
  weekly_consistency: number;
}

export default function HabitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const habitId = params.id as string;
  const [habit, setHabit] = useState<Habit | null>(null);
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({
    name: "",
    frequency: "",
    description: "",
  });
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const loadHabitDetail = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`/api/v1/habits/${habitId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        setError("Habit not found");
        return;
      }

      const habitData = await res.json();
      setHabit(habitData);
      setEditData({
        name: habitData.name,
        frequency: habitData.frequency,
        description: habitData.description || "",
      });

      // Load stats
      const statsRes = await fetch(`/api/v1/habits/${habitId}/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (_err) {
      setError("Failed to load habit");
    } finally {
      setLoading(false);
    }
  }, [token, habitId]);

  useEffect(() => {
    if (!token) return;
    loadHabitDetail();
  }, [token, habitId, loadHabitDetail]);

  const markComplete = async () => {
    try {
      const res = await fetch(`/api/v1/habits/${habitId}/complete`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        await loadHabitDetail();
      }
    } catch (_err) {
      setError("Failed to mark habit complete");
    }
  };

  const saveEdit = async () => {
    try {
      const res = await fetch(`/api/v1/habits/${habitId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: editData.name,
          frequency: editData.frequency,
          description: editData.description || undefined,
        }),
      });

      if (res.ok) {
        const updated = await res.json();
        setHabit(updated);
        setEditMode(false);
      } else {
        setError("Failed to update habit");
      }
    } catch (_err) {
      setError("Failed to update habit");
    }
  };

  const deleteHabit = async () => {
    if (!confirm("Are you sure you want to delete this habit?")) return;

    try {
      const res = await fetch(`/api/v1/habits/${habitId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        router.push("/habits");
      } else {
        setError("Failed to delete habit");
      }
    } catch (_err) {
      setError("Failed to delete habit");
    }
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;
  if (!habit)
    return (
      <div style={{ padding: "20px", color: "red" }}>
        {error || "Habit not found"}
      </div>
    );

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", padding: "20px" }}>
      <div style={{ marginBottom: "20px" }}>
        <Link
          href="/habits"
          style={{ color: "#007bff", textDecoration: "none" }}
        >
          ← Back to Habits
        </Link>
      </div>

      {error && (
        <div style={{ color: "red", marginBottom: "10px" }}>{error}</div>
      )}

      {editMode ? (
        <div
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "8px",
          }}
        >
          <h2>Edit Habit</h2>
          <input
            type="text"
            value={editData.name}
            onChange={(e) => setEditData({ ...editData, name: e.target.value })}
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          />
          <select
            value={editData.frequency}
            onChange={(e) =>
              setEditData({ ...editData, frequency: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
            }}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="custom">Custom</option>
          </select>
          <textarea
            value={editData.description}
            onChange={(e) =>
              setEditData({ ...editData, description: e.target.value })
            }
            style={{
              width: "100%",
              padding: "8px",
              marginBottom: "10px",
              borderRadius: "4px",
              border: "1px solid #ddd",
              boxSizing: "border-box",
              minHeight: "80px",
            }}
          />
          <button
            onClick={saveEdit}
            style={{
              padding: "8px 16px",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              marginRight: "10px",
            }}
          >
            Save
          </button>
          <button
            onClick={() => setEditMode(false)}
            style={{
              padding: "8px 16px",
              backgroundColor: "#6c757d",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      ) : (
        <div>
          <h1>{habit.name}</h1>
          <div style={{ color: "#666", marginBottom: "10px" }}>
            <p>
              Frequency: <strong>{habit.frequency}</strong>
            </p>
            {habit.description && <p>Description: {habit.description}</p>}
            <p>Status: {habit.is_active ? "Active" : "Inactive"}</p>
          </div>

          {stats && (
            <div
              style={{
                border: "1px solid #ddd",
                padding: "15px",
                borderRadius: "8px",
                marginBottom: "20px",
                backgroundColor: "#f9f9f9",
              }}
            >
              <h2>Statistics</h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "15px",
                }}
              >
                <div>
                  <strong>Current Streak</strong>
                  <p
                    style={{
                      fontSize: "28px",
                      color: "#007bff",
                      margin: "5px 0",
                    }}
                  >
                    {stats.current_streak}
                  </p>
                </div>
                <div>
                  <strong>Longest Streak</strong>
                  <p
                    style={{
                      fontSize: "28px",
                      color: "#6c757d",
                      margin: "5px 0",
                    }}
                  >
                    {stats.longest_streak}
                  </p>
                </div>
                <div>
                  <strong>Completion Rate</strong>
                  <p style={{ fontSize: "20px", margin: "5px 0" }}>
                    {(stats.completion_rate * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <strong>Weekly Consistency</strong>
                  <p style={{ fontSize: "20px", margin: "5px 0" }}>
                    {(stats.weekly_consistency * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={markComplete}
            style={{
              padding: "10px 20px",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              marginRight: "10px",
              fontSize: "16px",
            }}
          >
            Mark Complete Today
          </button>
          <button
            onClick={() => setEditMode(true)}
            style={{
              padding: "10px 20px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              marginRight: "10px",
            }}
          >
            Edit
          </button>
          <button
            onClick={deleteHabit}
            style={{
              padding: "10px 20px",
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
      )}
    </div>
  );
}
