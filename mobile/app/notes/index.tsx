/**
 * KOROBOS — Notes list page.
 * Wraps NotesListScreen with expo-router compatible navigation props.
 */

import { useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import React, { useEffect, useState } from "react";
import NotesListScreen from "../../src/screens/NotesListScreen";
import type { Note } from "../../src/types/notes";

export default function NotesPage() {
  const router = useRouter();
  const [token, setToken] = useState("");

  useEffect(() => {
    SecureStore.getItemAsync("auth_token").then((t) => setToken(t ?? ""));
  }, []);

  return (
    <NotesListScreen
      token={token}
      onSelectNote={(note: Note) => router.push(`/notes/${note.id}`)}
      onCreateNote={() => router.push("/notes/new")}
    />
  );
}
