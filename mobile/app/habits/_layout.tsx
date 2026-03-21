/**
 * KOROBOS — Habits stack layout.
 */

import { Stack } from "expo-router";
import React from "react";

export default function HabitsLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#007bff" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "600" },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Habits" }} />
      <Stack.Screen name="[habitId]" options={{ title: "Habit" }} />
    </Stack>
  );
}
