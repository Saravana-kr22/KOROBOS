/**
 * KOROBOS — Notes list page.
 * Wraps NotesListScreen with expo-router compatible navigation props.
 */

import { useRouter } from "expo-router";
import React from "react";
import NotesListScreen from "../../src/screens/NotesListScreen";

export default function NotesPage() {
  const router = useRouter();
  const navigation = {
    navigate: (name: string, params?: any) => {
      if (name === "NoteEditor") {
        router.push(`/notes/${params?.noteId ?? "new"}`);
      }
    },
    goBack: () => router.back(),
  };
  return (
    <NotesListScreen navigation={navigation} route={{ params: {} } as any} />
  );
}
