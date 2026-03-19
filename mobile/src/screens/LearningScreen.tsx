/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Learning Screen — timer, quick log, stats, and session history.
 * Supports offline manual logging via AsyncStorage queue.
 * Supports background timer persistence via AppState listener.
 */

import { useRouter } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  AppState,
  AppStateStatus,
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import { learningApi } from "../services/learningApi";
import {
  clearSyncedLogs,
  getPendingCount,
  queueSessionLog,
  syncPendingSessionLogs,
} from "../services/learningOfflineQueue";
import {
  cancelTimerNotification,
  showTimerNotification,
} from "../services/BackgroundTimerService";
import { useStudyReminder } from "../hooks/useStudyReminder";
import { LearningSession, LearningStats, Topic } from "../types/learning";

export default function LearningScreen() {
  const router = useRouter();
  const { reminderState, setReminder, clearReminder } = useStudyReminder();

  // Reminder form state
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderHour, setReminderHour] = useState("09");
  const [reminderMinute, setReminderMinute] = useState("00");

  const [sessions, setSessions] = useState<LearningSession[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [activeSession, setActiveSession] = useState<LearningSession | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [pendingCount, setPendingCount] = useState(0);

  // Timer state
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Background timer: record the timestamp when app goes to background
  const backgroundTimeRef = useRef<number | null>(null);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);

  // Quick log form
  const [showLogForm, setShowLogForm] = useState(false);
  const [logTopic, setLogTopic] = useState("");
  const [logDuration, setLogDuration] = useState("");
  const [logNotes, setLogNotes] = useState("");

  const [showStartForm, setShowStartForm] = useState(false);
  const [startTopic, setStartTopic] = useState("");

  // Suggestions
  const [filteredTopics, setFilteredTopics] = useState<Topic[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleTopicChange = (text: string, type: "start" | "log") => {
    if (type === "start") setStartTopic(text);
    else setLogTopic(text);

    if (text.length > 0) {
      const filtered = topics.filter((t) =>
        t.name.toLowerCase().includes(text.toLowerCase()),
      );
      setFilteredTopics(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const selectTopicSuggestion = (topicName: string, type: "start" | "log") => {
    if (type === "start") setStartTopic(topicName);
    else setLogTopic(topicName);
    setShowSuggestions(false);
  };

  const loadData = useCallback(async () => {
    try {
      setError("");
      const [sessRes, statsRes, topicsRes] = await Promise.all([
        learningApi.listSessions(0, 20),
        learningApi.getStats(),
        learningApi.listTopics(),
      ]);

      const all = sessRes.sessions;
      setSessions(all);
      setStats(statsRes);
      setTopics(topicsRes.topics || []);

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
      } else {
        setActiveSession(null);
      }
    } catch (err) {
      setError("Failed to load learning data");
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const syncOfflineQueue = useCallback(async () => {
    const count = await syncPendingSessionLogs();
    if (count > 0) {
      await clearSyncedLogs();
      await loadData();
    }
    const remaining = await getPendingCount();
    setPendingCount(remaining);
  }, [loadData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useFocusEffect(
    useCallback(() => {
      syncOfflineQueue().catch((err) =>
        console.warn("Failed to sync offline queue:", err),
      );
    }, [syncOfflineQueue]),
  );

  // Background timer persistence via AppState
  useEffect(() => {
    const handleAppStateChange = (nextState: AppStateStatus) => {
      const prevState = appStateRef.current;
      appStateRef.current = nextState;

      if (
        prevState === "active" &&
        (nextState === "background" || nextState === "inactive")
      ) {
        // App going to background: record the time and show persistent notification
        backgroundTimeRef.current = Date.now();
        if (activeSession?.status === "active") {
          showTimerNotification(activeSession.topic, elapsed).catch((err) =>
            console.warn("Failed to show timer notification:", err),
          );
        }
      } else if (nextState === "active" && backgroundTimeRef.current !== null) {
        // App coming back to foreground: add elapsed background time and cancel notification
        const backgroundElapsed = Math.floor(
          (Date.now() - backgroundTimeRef.current) / 1000,
        );
        backgroundTimeRef.current = null;
        cancelTimerNotification().catch((err) =>
          console.warn("Failed to cancel timer notification:", err),
        );
        if (activeSession?.status === "active") {
          setElapsed((e) => e + backgroundElapsed);
        }
      }
    };

    const subscription = AppState.addEventListener(
      "change",
      handleAppStateChange,
    );
    return () => subscription.remove();
  }, [activeSession?.status, activeSession?.topic, elapsed]);

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
    if (h > 0) {
      return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    }
    return `${m}:${String(s).padStart(2, "0")}`;
  };

  const handleStartSession = async () => {
    if (!startTopic.trim()) {
      Alert.alert("Error", "Topic is required");
      return;
    }
    try {
      await learningApi.startSession({ topic: startTopic.trim() });
      setStartTopic("");
      setShowStartForm(false);
      await loadData();
    } catch (err: any) {
      const msg = err?.message || "Failed to start session";
      Alert.alert("Error", msg);
    }
  };

  const handleStopSession = async () => {
    if (!activeSession) return;
    try {
      await cancelTimerNotification();
      await learningApi.stopSession({ session_id: activeSession.id });
      setActiveSession(null);
      setElapsed(0);
      await loadData();
    } catch (err) {
      Alert.alert("Error", "Failed to stop session");
    }
  };

  const handlePauseSession = async () => {
    if (!activeSession) return;
    try {
      await cancelTimerNotification();
      const updated = await learningApi.pauseSession({
        session_id: activeSession.id,
      });
      setActiveSession(updated);
    } catch (err) {
      Alert.alert("Error", "Failed to pause session");
    }
  };

  const handleResumeSession = async () => {
    if (!activeSession) return;
    try {
      const updated = await learningApi.resumeSession({
        session_id: activeSession.id,
      });
      setActiveSession(updated);
    } catch (err) {
      Alert.alert("Error", "Failed to resume session");
    }
  };

  const handleLogSession = async () => {
    if (!logTopic.trim() || !logDuration) {
      Alert.alert("Error", "Topic and duration are required");
      return;
    }
    const payload = {
      topic: logTopic.trim(),
      duration: parseInt(logDuration),
      notes: logNotes.trim() || undefined,
    };
    try {
      await learningApi.logSession(payload);
      setLogTopic("");
      setLogDuration("");
      setLogNotes("");
      setShowLogForm(false);
      await loadData();
    } catch (err) {
      // Offline fallback
      try {
        await queueSessionLog(payload);
        const remaining = await getPendingCount();
        setPendingCount(remaining);
        setLogTopic("");
        setLogDuration("");
        setLogNotes("");
        setShowLogForm(false);
        Alert.alert(
          "Saved Offline",
          "Session saved locally and will sync when you're back online.",
        );
      } catch {
        Alert.alert("Error", "Failed to save session");
      }
    }
  };

  const handleSetReminder = async () => {
    const h = parseInt(reminderHour, 10);
    const m = parseInt(reminderMinute, 10);
    if (isNaN(h) || h < 0 || h > 23 || isNaN(m) || m < 0 || m > 59) {
      Alert.alert(
        "Invalid time",
        "Enter a valid hour (0-23) and minute (0-59).",
      );
      return;
    }
    try {
      await setReminder(h, m);
      setShowReminderForm(false);
      Alert.alert(
        "Reminder Set",
        `You'll be reminded to study daily at ${String(h).padStart(
          2,
          "0",
        )}:${String(m).padStart(2, "0")}.`,
      );
    } catch (err: any) {
      Alert.alert("Error", err?.message || "Failed to set reminder");
    }
  };

  const handleClearReminder = () => {
    Alert.alert("Remove Reminder", "Cancel your daily study reminder?", [
      { text: "Keep it", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: async () => {
          await clearReminder();
        },
      },
    ]);
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Pending sync banner */}
      {pendingCount > 0 && (
        <View style={styles.syncBanner}>
          <Text style={styles.syncBannerText}>
            {pendingCount} session{pendingCount > 1 ? "s" : ""} pending sync
          </Text>
          <TouchableOpacity onPress={syncOfflineQueue}>
            <Text style={styles.syncBannerAction}>Sync now</Text>
          </TouchableOpacity>
        </View>
      )}

      {error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {/* Active session timer */}
      {activeSession && (
        <View
          style={[
            styles.timerCard,
            activeSession.status === "active"
              ? styles.timerCardActive
              : styles.timerCardPaused,
          ]}
        >
          <Text style={styles.timerTopic}>{activeSession.topic}</Text>
          <Text style={styles.timerClock}>{formatElapsed(elapsed)}</Text>
          <Text style={styles.timerStatus}>
            {activeSession.status === "active" ? "Running" : "Paused"}
          </Text>
          <View style={styles.timerButtons}>
            {activeSession.status === "active" && (
              <TouchableOpacity
                style={[styles.timerBtn, styles.timerBtnPause]}
                onPress={handlePauseSession}
              >
                <Text style={styles.timerBtnText}>Pause</Text>
              </TouchableOpacity>
            )}
            {activeSession.status === "paused" && (
              <TouchableOpacity
                style={[styles.timerBtn, styles.timerBtnResume]}
                onPress={handleResumeSession}
              >
                <Text style={styles.timerBtnText}>Resume</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[styles.timerBtn, styles.timerBtnStop]}
              onPress={handleStopSession}
            >
              <Text style={styles.timerBtnText}>Stop</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Start timer form */}
      {showStartForm && !activeSession && (
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Start Timer Session</Text>
          <TextInput
            style={styles.input}
            placeholder="Topic"
            value={startTopic}
            onChangeText={(t) => handleTopicChange(t, "start")}
            autoFocus
          />
          {showSuggestions && startTopic.length > 0 && (
            <View style={styles.suggestionList}>
              {filteredTopics.map((t) => (
                <TouchableOpacity
                  key={t.id}
                  style={styles.suggestionItem}
                  onPress={() => selectTopicSuggestion(t.name, "start")}
                >
                  <Text style={styles.suggestionText}>{t.name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          <View style={styles.formButtons}>
            <TouchableOpacity
              style={[styles.btn, styles.btnPrimary]}
              onPress={handleStartSession}
            >
              <Text style={styles.btnText}>Start</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.btnSecondary]}
              onPress={() => setShowStartForm(false)}
            >
              <Text style={styles.btnTextDark}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Manual log form */}
      {showLogForm && (
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Log a Session</Text>
          <TextInput
            style={styles.input}
            placeholder="Topic"
            value={logTopic}
            onChangeText={(t) => handleTopicChange(t, "log")}
            autoFocus
          />
          {showSuggestions && logTopic.length > 0 && (
            <View style={styles.suggestionList}>
              {filteredTopics.map((t) => (
                <TouchableOpacity
                  key={t.id}
                  style={styles.suggestionItem}
                  onPress={() => selectTopicSuggestion(t.name, "log")}
                >
                  <Text style={styles.suggestionText}>{t.name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          <TextInput
            style={styles.input}
            placeholder="Duration (minutes)"
            value={logDuration}
            onChangeText={setLogDuration}
            keyboardType="numeric"
          />
          <TextInput
            style={[styles.input, styles.inputMultiline]}
            placeholder="Notes (optional)"
            value={logNotes}
            onChangeText={setLogNotes}
            multiline
            numberOfLines={3}
          />
          <View style={styles.formButtons}>
            <TouchableOpacity
              style={[styles.btn, styles.btnSuccess]}
              onPress={handleLogSession}
            >
              <Text style={styles.btnText}>Log</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.btnSecondary]}
              onPress={() => setShowLogForm(false)}
            >
              <Text style={styles.btnTextDark}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Stats */}
      {stats && (
        <View style={styles.statsGrid}>
          {[
            { label: "Total Sessions", value: String(stats.total_sessions) },
            { label: "Total Minutes", value: String(stats.total_minutes) },
            { label: "Today", value: `${stats.sessions_today} sessions` },
            { label: "Streak", value: `${stats.current_streak} days` },
            { label: "This Week", value: `${stats.weekly_minutes} min` },
            { label: "Topics", value: String(stats.topics.length) },
          ].map((s) => (
            <View key={s.label} style={styles.statCard}>
              <Text style={styles.statValue}>{s.value}</Text>
              <Text style={styles.statLabel}>{s.label}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Sessions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Sessions</Text>
        {sessions.length === 0 ? (
          <Text style={styles.emptyText}>
            No sessions yet. Start a timer or log a session.
          </Text>
        ) : (
          sessions.map((s) => (
            <TouchableOpacity
              key={s.id}
              style={styles.sessionCard}
              onPress={() => router.push(`/learning/${s.id}`)}
            >
              <View style={styles.sessionHeader}>
                <Text style={styles.sessionTopic}>{s.topic}</Text>
                <View
                  style={[
                    styles.statusBadge,
                    s.status === "completed"
                      ? styles.statusCompleted
                      : s.status === "active"
                      ? styles.statusActive
                      : styles.statusPaused,
                  ]}
                >
                  <Text style={styles.statusText}>{s.status}</Text>
                </View>
              </View>
              <Text style={styles.sessionMeta}>
                {s.duration} min · {new Date(s.created_at).toLocaleDateString()}
              </Text>
              {s.notes ? (
                <Text style={styles.sessionNotes} numberOfLines={1}>
                  {s.notes}
                </Text>
              ) : null}
            </TouchableOpacity>
          ))
        )}
      </View>

      {/* Daily reminder */}
      <View style={styles.reminderCard}>
        <View style={styles.reminderHeader}>
          <Text style={styles.reminderTitle}>Daily Reminder</Text>
          {reminderState.isSet ? (
            <TouchableOpacity onPress={handleClearReminder}>
              <Text style={styles.reminderClear}>Remove</Text>
            </TouchableOpacity>
          ) : null}
        </View>

        {reminderState.isSet ? (
          <Text style={styles.reminderActive}>
            ⏰ Reminding you daily at{" "}
            {String(reminderState.hour).padStart(2, "0")}:
            {String(reminderState.minute).padStart(2, "0")}
          </Text>
        ) : (
          <TouchableOpacity onPress={() => setShowReminderForm((v) => !v)}>
            <Text style={styles.reminderSet}>
              {showReminderForm ? "Cancel" : "Set a daily study reminder"}
            </Text>
          </TouchableOpacity>
        )}

        {showReminderForm && !reminderState.isSet && (
          <View style={styles.reminderForm}>
            <View style={styles.reminderTimeRow}>
              <TextInput
                style={styles.reminderTimeInput}
                value={reminderHour}
                onChangeText={setReminderHour}
                keyboardType="numeric"
                maxLength={2}
                placeholder="HH"
              />
              <Text style={styles.reminderColon}>:</Text>
              <TextInput
                style={styles.reminderTimeInput}
                value={reminderMinute}
                onChangeText={setReminderMinute}
                keyboardType="numeric"
                maxLength={2}
                placeholder="MM"
              />
              <TouchableOpacity
                style={[styles.btn, styles.btnPrimary, styles.reminderSaveBtn]}
                onPress={handleSetReminder}
              >
                <Text style={styles.btnText}>Save</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.reminderHint}>24-hour format (e.g. 09:00)</Text>
          </View>
        )}
      </View>

      {/* Action buttons */}
      <View style={styles.actions}>
        {!activeSession && (
          <TouchableOpacity
            style={[styles.btn, styles.btnPrimary, styles.btnFull]}
            onPress={() => {
              setShowStartForm(!showStartForm);
              setShowLogForm(false);
            }}
          >
            <Text style={styles.btnText}>
              {showStartForm ? "Cancel" : "Start Timer"}
            </Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.btn, styles.btnSecondary, styles.btnFull]}
          onPress={() => {
            setShowLogForm(!showLogForm);
            setShowStartForm(false);
          }}
        >
          <Text style={styles.btnTextDark}>
            {showLogForm ? "Cancel" : "Log Session"}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.btn, styles.btnOutline, styles.btnFull]}
          onPress={() => router.push("/learning/topics")}
        >
          <Text style={styles.btnTextDark}>Manage Topics</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  errorContainer: { padding: 16 },
  errorText: { color: "#dc3545", fontSize: 14 },

  syncBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#fff3cd",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#ffc107",
  },
  syncBannerText: { color: "#856404", fontSize: 13 },
  syncBannerAction: { color: "#007bff", fontSize: 13, fontWeight: "600" },

  timerCard: {
    margin: 12,
    padding: 20,
    borderRadius: 12,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  timerCardActive: { backgroundColor: "#e8f5e9" },
  timerCardPaused: { backgroundColor: "#fff8e1" },
  timerTopic: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  timerClock: {
    fontSize: 48,
    fontFamily: "monospace",
    fontWeight: "bold",
    color: "#212529",
    marginBottom: 4,
  },
  timerStatus: { fontSize: 13, color: "#666", marginBottom: 16 },
  timerButtons: { flexDirection: "row", gap: 10 },
  timerBtn: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  timerBtnPause: { backgroundColor: "#ffc107" },
  timerBtnResume: { backgroundColor: "#17a2b8" },
  timerBtnStop: { backgroundColor: "#dc3545" },
  timerBtnText: { color: "#fff", fontWeight: "600", fontSize: 15 },

  formCard: {
    margin: 12,
    padding: 16,
    backgroundColor: "#fff",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#ddd",
  },
  formTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
    color: "#333",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    padding: 10,
    marginBottom: 10,
    fontSize: 15,
    backgroundColor: "#fafafa",
  },
  inputMultiline: { minHeight: 70, textAlignVertical: "top" },
  formButtons: { flexDirection: "row", gap: 10 },

  suggestionList: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#eee",
    borderRadius: 8,
    marginTop: -8,
    marginBottom: 10,
    maxHeight: 150,
  },
  suggestionItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f5f5f5",
  },
  suggestionText: {
    fontSize: 14,
    color: "#007bff",
  },

  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 8,
    marginBottom: 8,
  },
  statCard: {
    width: "30%",
    margin: "1.5%",
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#eee",
  },
  statValue: { fontSize: 18, fontWeight: "bold", color: "#212529" },
  statLabel: { fontSize: 10, color: "#666", marginTop: 4, textAlign: "center" },

  section: { paddingHorizontal: 12, marginBottom: 12 },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#212529",
    marginBottom: 10,
  },
  emptyText: {
    color: "#999",
    fontSize: 14,
    textAlign: "center",
    paddingVertical: 20,
  },

  sessionCard: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#eee",
  },
  sessionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  sessionTopic: { fontSize: 15, fontWeight: "600", color: "#333", flex: 1 },
  sessionMeta: { fontSize: 13, color: "#666" },
  sessionNotes: {
    fontSize: 12,
    color: "#999",
    marginTop: 4,
    fontStyle: "italic",
  },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  statusCompleted: { backgroundColor: "#e8f5e9" },
  statusActive: { backgroundColor: "#e3f2fd" },
  statusPaused: { backgroundColor: "#fff8e1" },
  statusText: { fontSize: 11, fontWeight: "600" },

  reminderCard: {
    marginHorizontal: 12,
    marginBottom: 12,
    padding: 14,
    backgroundColor: "#fff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#eee",
  },
  reminderHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  reminderTitle: { fontSize: 14, fontWeight: "600", color: "#333" },
  reminderClear: { fontSize: 13, color: "#dc3545" },
  reminderActive: { fontSize: 14, color: "#28a745" },
  reminderSet: { fontSize: 13, color: "#007bff" },
  reminderForm: { marginTop: 10 },
  reminderTimeRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  reminderTimeInput: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    padding: 8,
    width: 52,
    textAlign: "center",
    fontSize: 16,
    backgroundColor: "#fafafa",
  },
  reminderColon: { fontSize: 20, fontWeight: "bold", color: "#333" },
  reminderSaveBtn: { marginLeft: 8, paddingVertical: 8, paddingHorizontal: 14 },
  reminderHint: { fontSize: 11, color: "#999", marginTop: 4 },

  actions: { paddingHorizontal: 12, paddingBottom: 24, gap: 8 },
  btn: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: "center",
  },
  btnFull: { width: "100%" },
  btnPrimary: { backgroundColor: "#007bff" },
  btnSuccess: { backgroundColor: "#28a745" },
  btnSecondary: { backgroundColor: "#e9ecef" },
  btnOutline: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: "#aaa",
  },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 15 },
  btnTextDark: { color: "#333", fontWeight: "600", fontSize: 15 },
});
