/**
 * KOROBOS — Note editor page (dynamic route).
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React from "react";
import NoteEditorScreen from "../../src/screens/NoteEditorScreen";

export default function NoteEditorPage() {
  const router = useRouter();
  const { noteId } = useLocalSearchParams<{ noteId: string }>();
  const navigation = {
    navigate: (name: string, params?: any) =>
      router.push(`/notes/${params?.noteId ?? "new"}`),
    goBack: () => router.back(),
    setOptions: (_opts: any) => {},
  };
  const route = { params: { noteId } } as any;
  return <NoteEditorScreen navigation={navigation} route={route} />;
}
