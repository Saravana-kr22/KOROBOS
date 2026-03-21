/**
 * KOROBOS — Notes stack layout.
 */

import { Stack } from "expo-router";
import React from "react";

export default function NotesLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#007bff" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "600" },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Notes" }} />
      <Stack.Screen name="[noteId]" options={{ title: "Note" }} />
    </Stack>
  );
}
