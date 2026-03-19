/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Learning Session Detail Screen — view details, linked notes, delete.
 * Supports linking and unlinking knowledge-base notes to the session.
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { learningApi } from "../services/learningApi";
import { LearningSession } from "../types/learning";

export default function LearningSessionDetailScreen() {
  const router = useRouter();
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();

  const [session, setSession] = useState<LearningSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  // Note linking state
  const [linkedNoteIds, setLinkedNoteIds] = useState<string[]>([]);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [newNoteId, setNewNoteId] = useState("");
  const [linkingNote, setLinkingNote] = useState(false);

  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    try {
      setError("");
      const [data, noteIds] = await Promise.all([
        learningApi.getSession(sessionId),
        learningApi.getSessionNotes(sessionId),
      ]);
      setSession(data);
      setLinkedNoteIds(noteIds);
    } catch (err) {
      setError("Failed to load session");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  const handleDelete = () => {
    Alert.alert(
      "Delete Session",
      "Are you sure you want to delete this session? This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            setDeleting(true);
            try {
              await learningApi.deleteSession(sessionId as string);
              router.back();
            } catch {
              Alert.alert("Error", "Failed to delete session");
              setDeleting(false);
            }
          },
        },
      ],
    );
  };

  const handleLinkNote = async () => {
    const trimmed = newNoteId.trim();
    if (!trimmed) return;
    setLinkingNote(true);
    try {
      await learningApi.linkNote(sessionId as string, trimmed);
      setNewNoteId("");
      setShowLinkForm(false);
      const noteIds = await learningApi.getSessionNotes(sessionId as string);
      setLinkedNoteIds(noteIds);
    } catch {
      Alert.alert(
        "Error",
        "Failed to link note. Check the note ID and try again.",
      );
    } finally {
      setLinkingNote(false);
    }
  };

  const handleUnlinkNote = (noteId: string) => {
    Alert.alert("Unlink Note", "Remove this note from the session?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: async () => {
          try {
            await learningApi.unlinkNote(sessionId as string, noteId);
            setLinkedNoteIds((ids) => ids.filter((id) => id !== noteId));
          } catch {
            Alert.alert("Error", "Failed to unlink note");
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  if (error || !session) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error || "Session not found"}</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backBtnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const statusColor =
    session.status === "completed"
      ? "#2e7d32"
      : session.status === "active"
      ? "#1565c0"
      : "#f57f17";

  const statusBg =
    session.status === "completed"
      ? "#e8f5e9"
      : session.status === "active"
      ? "#e3f2fd"
      : "#fff8e1";

  return (
    <ScrollView style={styles.container}>
      {/* Main details */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.topic}>{session.topic}</Text>
          <View style={[styles.badge, { backgroundColor: statusBg }]}>
            <Text style={[styles.badgeText, { color: statusColor }]}>
              {session.status}
            </Text>
          </View>
        </View>

        <View style={styles.metaGrid}>
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>Duration</Text>
            <Text style={styles.metaValue}>{session.duration} minutes</Text>
          </View>
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>Date</Text>
            <Text style={styles.metaValue}>
              {new Date(session.created_at).toLocaleDateString()}
            </Text>
          </View>
          {session.start_time && (
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Started</Text>
              <Text style={styles.metaValue}>
                {new Date(session.start_time).toLocaleTimeString()}
              </Text>
            </View>
          )}
          {session.end_time && (
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Ended</Text>
              <Text style={styles.metaValue}>
                {new Date(session.end_time).toLocaleTimeString()}
              </Text>
            </View>
          )}
        </View>

        {session.notes ? (
          <View style={styles.notesSection}>
            <Text style={styles.metaLabel}>Notes</Text>
            <Text style={styles.notesText}>{session.notes}</Text>
          </View>
        ) : null}
      </View>

      {/* Linked Notes */}
      <View style={styles.card}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Linked Notes</Text>
          <TouchableOpacity
            style={styles.linkBtn}
            onPress={() => setShowLinkForm((v) => !v)}
          >
            <Text style={styles.linkBtnText}>
              {showLinkForm ? "Cancel" : "+ Link Note"}
            </Text>
          </TouchableOpacity>
        </View>

        {showLinkForm && (
          <View style={styles.linkForm}>
            <TextInput
              style={styles.input}
              placeholder="Note ID (UUID)"
              value={newNoteId}
              onChangeText={setNewNoteId}
              autoFocus
              autoCapitalize="none"
              onSubmitEditing={handleLinkNote}
              returnKeyType="done"
            />
            <TouchableOpacity
              style={[
                styles.btn,
                styles.btnPrimary,
                linkingNote && styles.btnDisabled,
              ]}
              onPress={handleLinkNote}
              disabled={linkingNote}
            >
              <Text style={styles.btnText}>
                {linkingNote ? "Linking…" : "Link"}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {linkedNoteIds.length === 0 ? (
          <Text style={styles.emptyText}>No notes linked to this session.</Text>
        ) : (
          linkedNoteIds.map((noteId) => (
            <View key={noteId} style={styles.noteRow}>
              <Text style={styles.noteId} numberOfLines={1}>
                {noteId}
              </Text>
              <TouchableOpacity
                style={styles.unlinkBtn}
                onPress={() => handleUnlinkNote(noteId)}
              >
                <Text style={styles.unlinkBtnText}>Unlink</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
      </View>

      {/* Delete */}
      <TouchableOpacity
        style={styles.deleteBtn}
        onPress={handleDelete}
        disabled={deleting}
      >
        <Text style={styles.deleteBtnText}>
          {deleting ? "Deleting…" : "Delete Session"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  errorText: { color: "#dc3545", fontSize: 16, marginBottom: 12 },
  backBtn: { padding: 10 },
  backBtnText: { color: "#007bff", fontSize: 15 },

  card: {
    backgroundColor: "#fff",
    margin: 12,
    marginBottom: 0,
    borderRadius: 10,
    padding: 16,
    borderWidth: 1,
    borderColor: "#eee",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
  },
  topic: {
    fontSize: 20,
    fontWeight: "700",
    color: "#212529",
    flex: 1,
    marginRight: 10,
  },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { fontSize: 12, fontWeight: "600" },

  metaGrid: { flexDirection: "row", flexWrap: "wrap", marginBottom: 12 },
  metaItem: { width: "50%", marginBottom: 12 },
  metaLabel: { fontSize: 12, color: "#999", marginBottom: 2 },
  metaValue: { fontSize: 15, fontWeight: "500", color: "#333" },

  notesSection: {
    borderTopWidth: 1,
    borderTopColor: "#eee",
    paddingTop: 12,
    marginTop: 4,
  },
  notesText: { fontSize: 14, color: "#444", lineHeight: 20 },

  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#212529" },
  linkBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#e3f2fd",
    borderRadius: 6,
  },
  linkBtnText: { color: "#1565c0", fontSize: 13, fontWeight: "600" },

  linkForm: { marginBottom: 12 },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    padding: 10,
    marginBottom: 8,
    fontSize: 14,
    backgroundColor: "#fafafa",
    fontFamily: "monospace",
  },
  btn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: "center",
  },
  btnPrimary: { backgroundColor: "#007bff" },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 14 },

  emptyText: { fontSize: 13, color: "#999", fontStyle: "italic" },

  noteRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: "#f0f0f0",
  },
  noteId: {
    flex: 1,
    fontSize: 12,
    color: "#555",
    fontFamily: "monospace",
    marginRight: 8,
  },
  unlinkBtn: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: "#fff5f5",
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#dc3545",
  },
  unlinkBtnText: { color: "#dc3545", fontSize: 12, fontWeight: "600" },

  deleteBtn: {
    margin: 12,
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#dc3545",
    alignItems: "center",
  },
  deleteBtnText: { color: "#dc3545", fontWeight: "600", fontSize: 15 },
});
