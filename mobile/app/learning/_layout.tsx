/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Learning stack layout — handles navigation stack for learning screens.
 */

import { Stack } from "expo-router";
import React from "react";

export default function LearningLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#007bff" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "600" },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Learning" }} />
      <Stack.Screen name="topics" options={{ title: "Topics" }} />
      <Stack.Screen name="[sessionId]" options={{ title: "Session Detail" }} />
    </Stack>
  );
}
