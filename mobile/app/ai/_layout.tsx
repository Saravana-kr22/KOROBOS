/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * AI screens group layout — organizes insights and recommendations screens.
 */

import { Stack } from "expo-router";
import React from "react";

export default function AILayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen
        name="insights"
        options={{
          title: "Insights",
        }}
      />
      <Stack.Screen
        name="recommendations"
        options={{
          title: "Recommendations",
        }}
      />
    </Stack>
  );
}
