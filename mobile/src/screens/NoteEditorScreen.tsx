/**
 * KOROBOS — Second Brain Operating System
 * Copyright (c) 2026 Saravana Perumal K
 * Licensed under the GNU Affero General Public License v3.
 *
 * Note editor screen with markdown input and offline draft support — Sprint 6 §12.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useDrafts } from "../hooks/useNotes";
import * as NotesApi from "../services/notesApi";
import type { Note } from "../types/notes";

interface Props {
  token: string;
  /** When provided, the editor is in edit mode for an existing note. */
  note?: Note;
  onSaved: (note: Note) => void;
  onCancel: () => void;
}

export default function NoteEditorScreen({
  token,
  note,
  onSaved,
  onCancel,
}: Props) {
  const [title, setTitle] = useState(note?.title ?? "");
  const [content, setContent] = useState(note?.content_md ?? "");
  const [tagInput, setTagInput] = useState(note?.tags.join(", ") ?? "");
  const [saving, setSaving] = useState(false);

  const { saveDraft } = useDrafts();

  const parsedTags = tagInput
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const handleSave = useCallback(async () => {
    if (!title.trim()) {
      Alert.alert("Validation", "Title is required.");
      return;
    }
    setSaving(true);
    try {
      let saved: Note;
      if (note) {
        saved = await NotesApi.updateNote(token, note.id, {
          title: title.trim(),
          content_md: content,
          tags: parsedTags,
        });
      } else {
        saved = await NotesApi.createNote(token, {
          title: title.trim(),
          content_md: content,
          tags: parsedTags,
        });
      }
      onSaved(saved);
    } catch (e) {
      Alert.alert(
        "Save failed",
        e instanceof Error ? e.message : "Unknown error",
      );
    } finally {
      setSaving(false);
    }
  }, [token, note, title, content, parsedTags, onSaved]);

  /** Save offline draft when network is unavailable. */
  const handleSaveDraft = useCallback(async () => {
    await saveDraft({
      title: title.trim() || "Untitled",
      content_md: content,
      tags: parsedTags,
    });
    Alert.alert(
      "Saved offline",
      "Draft saved locally — will sync when online.",
    );
    onCancel();
  }, [saveDraft, title, content, parsedTags, onCancel]);

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.toolbar}>
        <Pressable onPress={onCancel} style={styles.toolbarBtn}>
          <Text style={styles.toolbarBtnText}>Cancel</Text>
        </Pressable>
        <Text style={styles.toolbarTitle}>
          {note ? "Edit Note" : "New Note"}
        </Text>
        <Pressable
          onPress={handleSave}
          style={[styles.toolbarBtn, styles.saveBtn]}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={[styles.toolbarBtnText, styles.saveBtnText]}>
              Save
            </Text>
          )}
        </Pressable>
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Title</Text>
        <TextInput
          style={styles.titleInput}
          value={title}
          onChangeText={setTitle}
          placeholder="Note title..."
          placeholderTextColor="#9ca3af"
          maxLength={500}
        />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Tags (comma-separated)</Text>
        <TextInput
          style={styles.input}
          value={tagInput}
          onChangeText={setTagInput}
          placeholder="ml, ai, learning"
          placeholderTextColor="#9ca3af"
          autoCapitalize="none"
        />
      </View>

      <View style={[styles.field, styles.editorField]}>
        <Text style={styles.label}>Content (Markdown)</Text>
        <Text style={styles.hint}>
          Use [[Note Title]] to create wiki-links between notes.
        </Text>
        <TextInput
          style={styles.markdownInput}
          value={content}
          onChangeText={setContent}
          placeholder={
            "# Your note\n\nStart writing in markdown...\n\nLink to other notes with [[Note Title]]"
          }
          placeholderTextColor="#9ca3af"
          multiline
          textAlignVertical="top"
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      <Pressable onPress={handleSaveDraft} style={styles.draftBtn}>
        <Text style={styles.draftBtnText}>Save as offline draft</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  toolbar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    borderBottomWidth: 1,
    borderColor: "#eee",
  },
  toolbarTitle: { fontWeight: "700", fontSize: 16 },
  toolbarBtn: { padding: 8, borderRadius: 8 },
  toolbarBtnText: { color: "#6366f1", fontWeight: "600" },
  saveBtn: { backgroundColor: "#6366f1" },
  saveBtnText: { color: "#fff" },
  field: { padding: 16, borderBottomWidth: 1, borderColor: "#f0f0f0" },
  editorField: { flex: 1 },
  label: { fontSize: 13, fontWeight: "600", color: "#6b7280", marginBottom: 6 },
  hint: { fontSize: 12, color: "#9ca3af", marginBottom: 8 },
  titleInput: { fontSize: 20, fontWeight: "700", color: "#111827" },
  input: {
    fontSize: 15,
    color: "#111827",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    padding: 10,
  },
  markdownInput: {
    fontFamily: "monospace",
    fontSize: 14,
    color: "#111827",
    minHeight: 300,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    padding: 12,
    lineHeight: 22,
  },
  draftBtn: {
    margin: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    alignItems: "center",
  },
  draftBtnText: { color: "#6b7280", fontWeight: "500" },
});
