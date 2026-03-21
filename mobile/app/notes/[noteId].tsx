/**
 * KOROBOS — Note editor page (dynamic route).
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useState } from "react";
import NoteEditorScreen from "../../src/screens/NoteEditorScreen";
import { useNote } from "../../src/hooks/useNotes";
import type { Note } from "../../src/types/notes";

export default function NoteEditorPage() {
  const router = useRouter();
  const { noteId } = useLocalSearchParams<{ noteId: string }>();
  const [token, setToken] = useState("");

  useEffect(() => {
    SecureStore.getItemAsync("auth_token").then((t) => setToken(t ?? ""));
  }, []);

  const isNew = !noteId || noteId === "new";
  const { note } = useNote(token, isNew ? "" : noteId);

  return (
    <NoteEditorScreen
      token={token}
      note={isNew ? undefined : note ?? undefined}
      onSaved={(_note: Note) => router.back()}
      onCancel={() => router.back()}
    />
  );
}
