/**
 * KOROBOS — Databases stack layout.
 */

import { Stack } from "expo-router";
import React from "react";

export default function DatabasesLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#007bff" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "600" },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Databases" }} />
      <Stack.Screen name="[databaseId]/index" options={{ title: "Database" }} />
      <Stack.Screen name="[databaseId]/kanban" options={{ title: "Kanban" }} />
      <Stack.Screen
        name="[databaseId]/calendar"
        options={{ title: "Calendar" }}
      />
    </Stack>
  );
}
