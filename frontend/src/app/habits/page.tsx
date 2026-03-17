"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";

interface HabitTodayItem {
  habit_id: string;
  name: string;
  completed: boolean;
}

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

export default function HabitsPage() {
  const [todayHabits, setTodayHabits] = useState<HabitTodayItem[]>([]);
  const [allHabits, setAllHabits] = useState<Habit[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    frequency: "daily",
    description: "",
  });
  const [error, setError] = useState("");
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const loadHabits = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Load today's habits
      const todayRes = await fetch("/api/v1/habits/today", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (todayRes.ok) {
        const data = await todayRes.json();
        setTodayHabits(data.habits || []);
      }

      // Load all habits
      const allRes = await fetch("/api/v1/habits?limit=100", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (allRes.ok) {
        const data = await allRes.json();
        setAllHabits(data.habits || []);
      }
    } catch (_err) {
      setError("Failed to load habits");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    loadHabits();
  }, [token, loadHabits]);

  const handleCreateHabit = async (e: FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("Habit name is required");
      return;
    }

    try {
      const res = await fetch("/api/v1/habits", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: formData.name,
          frequency: formData.frequency,
          description: formData.description || undefined,
        }),
      });

      if (res.ok) {
        setFormData({ name: "", frequency: "daily", description: "" });
        setShowForm(false);
        await loadHabits();
      } else {
        setError("Failed to create habit");
      }
    } catch (_err) {
      setError("Failed to create habit");
    }
  };

  const markComplete = async (habitId: string) => {
    try {
      const res = await fetch(`/api/v1/habits/${habitId}/complete`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        await loadHabits();
      }
    } catch (_err) {
      setError("Failed to mark habit complete");
    }
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "20px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h1>Habits</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "8px 16px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          {showForm ? "Cancel" : "New Habit"}
        </button>
      </div>

      {error && (
        <div style={{ color: "red", marginBottom: "10px" }}>{error}</div>
      )}

      {showForm && (
        <form
          onSubmit={handleCreateHabit}
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "8px",
            marginBottom: "20px",
          }}
        >
          <input
            type="text"
            placeholder="Habit name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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
            value={formData.frequency}
            onChange={(e) =>
              setFormData({ ...formData, frequency: e.target.value })
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
            placeholder="Description (optional)"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
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
            Create Habit
          </button>
        </form>
      )}

      <section style={{ marginBottom: "30px" }}>
        <h2>Today&apos;s Habits</h2>
        {todayHabits.length === 0 ? (
          <p style={{ color: "#666" }}>No habits for today</p>
        ) : (
          <div>
            {todayHabits.map((habit) => (
              <div
                key={habit.habit_id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px",
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  marginBottom: "8px",
                  backgroundColor: habit.completed ? "#f0f8f0" : "#fff",
                }}
              >
                <Link
                  href={`/habits/${habit.habit_id}`}
                  style={{ flex: 1, textDecoration: "none", color: "#333" }}
                >
                  <strong>{habit.name}</strong>
                </Link>
                <div
                  style={{ display: "flex", gap: "10px", alignItems: "center" }}
                >
                  {habit.completed && (
                    <span style={{ color: "green" }}>✓ Done</span>
                  )}
                  {!habit.completed && (
                    <button
                      onClick={() => markComplete(habit.habit_id)}
                      style={{
                        padding: "6px 12px",
                        backgroundColor: "#007bff",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                      }}
                    >
                      Mark Complete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2>All Habits ({allHabits.length})</h2>
        {allHabits.length === 0 ? (
          <p style={{ color: "#666" }}>No habits yet</p>
        ) : (
          <div>
            {allHabits.map((habit) => (
              <div
                key={habit.id}
                style={{
                  padding: "12px",
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  marginBottom: "8px",
                  cursor: "pointer",
                  textDecoration: "none",
                }}
                onClick={() => (window.location.href = `/habits/${habit.id}`)}
              >
                <strong>{habit.name}</strong>
                <div
                  style={{ fontSize: "14px", color: "#666", marginTop: "4px" }}
                >
                  {habit.frequency} • {habit.is_active ? "Active" : "Inactive"}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
