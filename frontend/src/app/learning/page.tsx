"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

interface LearningSession {
  id: string;
  user_id: string;
  topic: string;
  topic_id: string | null;
  duration: number;
  notes: string | null;
  status: string;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  updated_at: string;
}

interface LearningStats {
  total_sessions: number;
  total_minutes: number;
  topics: string[];
  sessions_today: number;
  current_streak: number;
  weekly_minutes: number;
  topic_distribution: Record<string, number>;
}

interface Topic {
  id: string;
  name: string;
}

export default function LearningPage() {
  const [sessions, setSessions] = useState<LearningSession[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showLogForm, setShowLogForm] = useState(false);
  const [showStartForm, setShowStartForm] = useState(false);
  const [activeSession, setActiveSession] = useState<LearningSession | null>(
    null,
  );
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [logForm, setLogForm] = useState({
    topic: "",
    duration: "",
    topic_id: "",
    notes: "",
  });
  const [startForm, setStartForm] = useState({
    topic: "",
    topic_id: "",
    notes: "",
  });

  // Daily Study Reminder state
  const [reminderEnabled, setReminderEnabled] = useState(false);
  const [reminderTime, setReminderTime] = useState("09:00");
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderMessage, setReminderMessage] = useState("");

  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const authHeaders = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [sessRes, statsRes, topicsRes] = await Promise.all([
        fetch("/api/v1/learning/sessions?limit=20", { headers: authHeaders }),
        fetch("/api/v1/learning/stats", { headers: authHeaders }),
        fetch("/api/v1/learning/topics", { headers: authHeaders }),
      ]);

      if (sessRes.ok) {
        const data = await sessRes.json();
        const all: LearningSession[] = data.sessions || [];
        setSessions(all);
        // Detect any active/paused session
        const active = all.find(
          (s) => s.status === "active" || s.status === "paused",
        );
        if (active) {
          setActiveSession(active);
          if (active.status === "active" && active.start_time) {
            const startMs = new Date(active.start_time).getTime();
            setElapsed(
              Math.floor((Date.now() - startMs) / 1000) + active.duration * 60,
            );
          } else {
            setElapsed(active.duration * 60);
          }
        }
      }
      if (statsRes.ok) setStats(await statsRes.json());
      if (topicsRes.ok) {
        const data = await topicsRes.json();
        setTopics(data.topics || []);
      }
    } catch {
      setError("Failed to load learning data");
    } finally {
      setLoading(false);
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!token) return;
    loadData();
  }, [token, loadData]);

  // Load persisted reminder state from localStorage and check if already sent today
  useEffect(() => {
    if (typeof window === "undefined") return;
    const enabled =
      localStorage.getItem("korobos:web_reminder_enabled") === "true";
    const time = localStorage.getItem("korobos:web_reminder_time") || "09:00";
    setReminderEnabled(enabled);
    setReminderTime(time);

    // On page load, fire immediately if past reminder time and not yet sent today
    if (enabled) {
      const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
      const lastSent = localStorage.getItem("korobos:web_reminder_last_sent");
      if (lastSent !== today) {
        const now = new Date();
        const [rHour, rMin] = time.split(":").map(Number);
        if (
          now.getHours() > rHour ||
          (now.getHours() === rHour && now.getMinutes() >= rMin)
        ) {
          // Past the reminder time today — fire immediately
          if (
            "Notification" in window &&
            Notification.permission === "granted"
          ) {
            new Notification("Time to learn! 📚", {
              body: "Your daily study session is waiting.",
              icon: "/favicon.ico",
            });
            localStorage.setItem("korobos:web_reminder_last_sent", today);
          }
        }
      }
    }
  }, []);

  // Check if current time matches reminder time (best-effort notification with deduplication)
  useEffect(() => {
    if (!reminderEnabled) return;
    const checkReminder = () => {
      const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
      const lastSent = localStorage.getItem("korobos:web_reminder_last_sent");
      if (lastSent === today) return; // Already fired today

      const now = new Date();
      const [rHour, rMin] = reminderTime.split(":").map(Number);
      const currentHour = now.getHours();
      const currentMin = now.getMinutes();
      // Fire if within a 5-minute window
      if (currentHour === rHour && Math.abs(currentMin - rMin) < 5) {
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("Time to learn! 📚", {
            body: "Your daily study session is waiting.",
            icon: "/favicon.ico",
          });
          localStorage.setItem("korobos:web_reminder_last_sent", today);
        }
      }
    };
    const interval = setInterval(checkReminder, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [reminderEnabled, reminderTime]);

  // Live timer tick
  useEffect(() => {
    if (activeSession?.status === "active") {
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [activeSession?.status]);

  const formatElapsed = (secs: number) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    return h > 0
      ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
      : `${m}:${String(s).padStart(2, "0")}`;
  };

  const handleLogSession = async (e: FormEvent) => {
    e.preventDefault();
    if (!logForm.topic.trim() || !logForm.duration) {
      setError("Topic and duration are required");
      return;
    }
    try {
      const body: Record<string, unknown> = {
        topic: logForm.topic,
        duration: parseInt(logForm.duration),
        notes: logForm.notes || undefined,
        topic_id: logForm.topic_id || undefined,
      };
      const res = await fetch("/api/v1/learning/sessions", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setLogForm({ topic: "", duration: "", topic_id: "", notes: "" });
        setShowLogForm(false);
        await loadData();
      } else {
        setError("Failed to log session");
      }
    } catch {
      setError("Failed to log session");
    }
  };

  const handleStartSession = async (e: FormEvent) => {
    e.preventDefault();
    if (!startForm.topic.trim()) {
      setError("Topic is required");
      return;
    }
    try {
      const body: Record<string, unknown> = {
        topic: startForm.topic,
        notes: startForm.notes || undefined,
        topic_id: startForm.topic_id || undefined,
      };
      const res = await fetch("/api/v1/learning/session/start", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const session = await res.json();
        setActiveSession(session);
        setElapsed(0);
        setStartForm({ topic: "", topic_id: "", notes: "" });
        setShowStartForm(false);
        await loadData();
      } else {
        const data = await res.json();
        setError(data?.detail?.message || "Failed to start session");
      }
    } catch {
      setError("Failed to start session");
    }
  };

  const handleStopSession = async () => {
    if (!activeSession) return;
    try {
      const res = await fetch("/api/v1/learning/session/stop", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ session_id: activeSession.id }),
      });
      if (res.ok) {
        setActiveSession(null);
        setElapsed(0);
        await loadData();
      } else {
        setError("Failed to stop session");
      }
    } catch {
      setError("Failed to stop session");
    }
  };

  const handlePauseSession = async () => {
    if (!activeSession) return;
    try {
      const res = await fetch("/api/v1/learning/session/pause", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ session_id: activeSession.id }),
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveSession(updated);
        await loadData();
      }
    } catch {
      setError("Failed to pause session");
    }
  };

  const handleResumeSession = async () => {
    if (!activeSession) return;
    try {
      const res = await fetch("/api/v1/learning/session/resume", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ session_id: activeSession.id }),
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveSession(updated);
        await loadData();
      }
    } catch {
      setError("Failed to resume session");
    }
  };

  const handleSaveReminder = async () => {
    try {
      // Request browser notification permission
      if ("Notification" in window) {
        if (Notification.permission === "default") {
          await Notification.requestPermission();
        }
      }
      // Save to localStorage
      localStorage.setItem("korobos:web_reminder_enabled", "true");
      localStorage.setItem("korobos:web_reminder_time", reminderTime);
      setReminderEnabled(true);
      setShowReminderForm(false);
      setReminderMessage(`Reminder set for ${reminderTime}`);
      setTimeout(() => setReminderMessage(""), 3000);
    } catch {
      setError("Failed to save reminder settings");
    }
  };

  const handleClearReminder = () => {
    localStorage.setItem("korobos:web_reminder_enabled", "false");
    setReminderEnabled(false);
    setReminderMessage("");
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: "960px", margin: "0 auto", padding: "20px" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <h1 style={{ margin: 0 }}>Learning</h1>
        <div style={{ display: "flex", gap: "10px" }}>
          <Link
            href="/learning/topics"
            style={{
              padding: "8px 14px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              textDecoration: "none",
              color: "#333",
            }}
          >
            Topics
          </Link>
          <button
            onClick={() => {
              setShowLogForm(!showLogForm);
              setShowStartForm(false);
            }}
            style={{
              padding: "8px 14px",
              backgroundColor: "#6c757d",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Log Session
          </button>
          <button
            onClick={() => {
              setShowStartForm(!showStartForm);
              setShowLogForm(false);
            }}
            style={{
              padding: "8px 14px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
            disabled={!!activeSession}
          >
            Start Timer
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: "red", marginBottom: "12px" }}>{error}</div>
      )}

      {/* Active Session Timer */}
      {activeSession && (
        <div
          style={{
            background:
              activeSession.status === "active" ? "#e8f5e9" : "#fff8e1",
            border: "1px solid #ccc",
            borderRadius: "8px",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: "bold", fontSize: "18px" }}>
                {activeSession.topic}
              </div>
              <div
                style={{
                  fontSize: "32px",
                  fontFamily: "monospace",
                  marginTop: "6px",
                }}
              >
                {formatElapsed(elapsed)}
              </div>
              <div
                style={{ fontSize: "13px", color: "#666", marginTop: "4px" }}
              >
                {activeSession.status === "active" ? "Running" : "Paused"}
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              {activeSession.status === "active" && (
                <button
                  onClick={handlePauseSession}
                  style={{
                    padding: "8px 14px",
                    backgroundColor: "#ffc107",
                    color: "#333",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  Pause
                </button>
              )}
              {activeSession.status === "paused" && (
                <button
                  onClick={handleResumeSession}
                  style={{
                    padding: "8px 14px",
                    backgroundColor: "#17a2b8",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  Resume
                </button>
              )}
              <button
                onClick={handleStopSession}
                style={{
                  padding: "8px 14px",
                  backgroundColor: "#dc3545",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Stop
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Start Session Form */}
      {showStartForm && !activeSession && (
        <form
          onSubmit={handleStartSession}
          style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <h3 style={{ margin: "0 0 12px" }}>Start Timer Session</h3>
          <input
            type="text"
            placeholder="Topic"
            value={startForm.topic}
            onChange={(e) =>
              setStartForm({ ...startForm, topic: e.target.value })
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
          <select
            value={startForm.topic_id}
            onChange={(e) =>
              setStartForm({ ...startForm, topic_id: e.target.value })
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
            <option value="">— Link to topic (optional) —</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <textarea
            placeholder="Notes (optional)"
            value={startForm.notes}
            onChange={(e) =>
              setStartForm({ ...startForm, notes: e.target.value })
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
            Start
          </button>
        </form>
      )}

      {/* Log Session Form */}
      {showLogForm && (
        <form
          onSubmit={handleLogSession}
          style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "16px",
            marginBottom: "20px",
          }}
        >
          <h3 style={{ margin: "0 0 12px" }}>Log a Session</h3>
          <input
            type="text"
            placeholder="Topic"
            value={logForm.topic}
            onChange={(e) => setLogForm({ ...logForm, topic: e.target.value })}
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
            placeholder="Duration (minutes)"
            value={logForm.duration}
            min={1}
            onChange={(e) =>
              setLogForm({ ...logForm, duration: e.target.value })
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
          <select
            value={logForm.topic_id}
            onChange={(e) =>
              setLogForm({ ...logForm, topic_id: e.target.value })
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
            <option value="">— Link to topic (optional) —</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <textarea
            placeholder="Notes (optional)"
            value={logForm.notes}
            onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
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
            Log
          </button>
        </form>
      )}

      {/* Stats */}
      {stats && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "12px",
            marginBottom: "24px",
          }}
        >
          {[
            { label: "Total Sessions", value: stats.total_sessions },
            { label: "Total Minutes", value: stats.total_minutes },
            { label: "Today", value: stats.sessions_today + " sessions" },
            { label: "Streak", value: stats.current_streak + " days" },
            { label: "This Week", value: stats.weekly_minutes + " min" },
            { label: "Topics", value: stats.topics.length },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                border: "1px solid #eee",
                borderRadius: "8px",
                padding: "14px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "22px", fontWeight: "bold" }}>
                {s.value}
              </div>
              <div
                style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}
              >
                {s.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Daily Study Reminder */}
      <div
        style={{
          border: "1px solid #e3f2fd",
          borderRadius: "8px",
          padding: "16px",
          marginBottom: "24px",
          backgroundColor: "#f8fbff",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
          }}
        >
          <h3 style={{ margin: 0 }}>Daily Study Reminder</h3>
          {reminderEnabled && (
            <button
              onClick={handleClearReminder}
              style={{
                padding: "4px 12px",
                fontSize: "12px",
                backgroundColor: "#fff",
                border: "1px solid #dc3545",
                borderRadius: "4px",
                color: "#dc3545",
                cursor: "pointer",
              }}
            >
              Clear
            </button>
          )}
        </div>
        {!reminderEnabled && !showReminderForm && (
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <input
              type="time"
              value={reminderTime}
              onChange={(e) => setReminderTime(e.target.value)}
              style={{
                padding: "6px 10px",
                borderRadius: "4px",
                border: "1px solid #ddd",
                fontFamily: "monospace",
              }}
            />
            <button
              onClick={handleSaveReminder}
              style={{
                padding: "6px 16px",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              Enable
            </button>
          </div>
        )}
        {reminderEnabled && (
          <div style={{ color: "#1565c0", fontSize: "14px" }}>
            Reminder set for {reminderTime}
          </div>
        )}
        {reminderMessage && (
          <div style={{ color: "#28a745", fontSize: "14px", marginTop: "8px" }}>
            ✓ {reminderMessage}
          </div>
        )}
      </div>

      {/* Sessions List */}
      <section>
        <h2 style={{ marginBottom: "12px" }}>
          Recent Sessions ({sessions.length})
        </h2>
        {sessions.length === 0 ? (
          <p style={{ color: "#666" }}>
            No sessions yet. Start a timer or log a session.
          </p>
        ) : (
          <div>
            {sessions.map((s) => (
              <div
                key={s.id}
                style={{
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  padding: "12px",
                  marginBottom: "8px",
                  cursor: "pointer",
                }}
                onClick={() => (window.location.href = `/learning/${s.id}`)}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <strong>{s.topic}</strong>
                  <span
                    style={{
                      fontSize: "12px",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      backgroundColor:
                        s.status === "completed"
                          ? "#e8f5e9"
                          : s.status === "active"
                          ? "#e3f2fd"
                          : "#fff8e1",
                      color:
                        s.status === "completed"
                          ? "#2e7d32"
                          : s.status === "active"
                          ? "#1565c0"
                          : "#f57f17",
                    }}
                  >
                    {s.status}
                  </span>
                </div>
                <div
                  style={{ fontSize: "13px", color: "#666", marginTop: "4px" }}
                >
                  {s.duration} min &bull;{" "}
                  {new Date(s.created_at).toLocaleDateString()}
                  {s.notes && (
                    <span>
                      {" "}
                      &bull; {s.notes.slice(0, 60)}
                      {s.notes.length > 60 ? "…" : ""}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
