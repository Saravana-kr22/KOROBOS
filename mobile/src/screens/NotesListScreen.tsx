/**
 * KOROBOS — Second Brain Operating System
 * Copyright (c) 2026 Saravana Perumal K
 * Licensed under the GNU Affero General Public License v3.
 *
 * Notes list screen — Sprint 6 §12.
 */

import React from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useNotesList } from "../hooks/useNotes";
import type { Note } from "../types/notes";

interface Props {
  token: string;
  onSelectNote: (note: Note) => void;
  onCreateNote: () => void;
}

export default function NotesListScreen({
  token,
  onSelectNote,
  onCreateNote,
}: Props) {
  const {
    notes,
    total,
    page,
    pages,
    loading,
    error,
    refresh,
    nextPage,
    prevPage,
  } = useNotesList(token);

  if (loading && notes.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{error}</Text>
        <Pressable style={styles.btn} onPress={refresh}>
          <Text style={styles.btnText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Notes ({total})</Text>
        <Pressable style={styles.btn} onPress={onCreateNote}>
          <Text style={styles.btnText}>+ New</Text>
        </Pressable>
      </View>

      <FlatList
        data={notes}
        keyExtractor={(n) => n.id}
        onRefresh={refresh}
        refreshing={loading}
        renderItem={({ item }) => (
          <Pressable style={styles.card} onPress={() => onSelectNote(item)}>
            <Text style={styles.noteTitle}>{item.title}</Text>
            {item.tags.length > 0 && (
              <View style={styles.tagRow}>
                {item.tags.map((t) => (
                  <Text key={t} style={styles.tag}>
                    #{t}
                  </Text>
                ))}
              </View>
            )}
            <Text style={styles.date}>
              {new Date(item.updated_at).toLocaleDateString()}
            </Text>
          </Pressable>
        )}
      />

      <View style={styles.pagination}>
        <Pressable
          onPress={prevPage}
          disabled={page <= 1}
          style={styles.pageBtn}
        >
          <Text>‹ Prev</Text>
        </Pressable>
        <Text style={styles.pageInfo}>
          {page} / {pages}
        </Text>
        <Pressable
          onPress={nextPage}
          disabled={page >= pages}
          style={styles.pageBtn}
        >
          <Text>Next ›</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    borderBottomWidth: 1,
    borderColor: "#eee",
  },
  title: { fontSize: 20, fontWeight: "700" },
  card: { padding: 16, borderBottomWidth: 1, borderColor: "#f0f0f0" },
  noteTitle: { fontSize: 16, fontWeight: "600", marginBottom: 4 },
  tagRow: { flexDirection: "row", flexWrap: "wrap", gap: 4, marginBottom: 4 },
  tag: {
    fontSize: 12,
    color: "#6366f1",
    backgroundColor: "#eef2ff",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  date: { fontSize: 12, color: "#9ca3af" },
  btn: {
    backgroundColor: "#6366f1",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  btnText: { color: "#fff", fontWeight: "600" },
  pagination: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    borderTopWidth: 1,
    borderColor: "#eee",
  },
  pageBtn: { padding: 8 },
  pageInfo: { fontWeight: "600" },
  error: { color: "#ef4444", marginBottom: 12 },
});
