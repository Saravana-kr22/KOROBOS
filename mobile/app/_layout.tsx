/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Root layout — bottom tab navigation for KOROBOS mobile.
 */

import { Tabs } from "expo-router";
import React from "react";

export default function RootLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#007bff",
        tabBarInactiveTintColor: "#999",
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarLabel: "Dashboard",
        }}
      />
      <Tabs.Screen
        name="learning"
        options={{
          title: "Learning",
          tabBarLabel: "Learning",
        }}
      />
      <Tabs.Screen
        name="notes"
        options={{
          title: "Notes",
          tabBarLabel: "Notes",
        }}
      />
      <Tabs.Screen
        name="habits"
        options={{
          title: "Habits",
          tabBarLabel: "Habits",
        }}
      />
      <Tabs.Screen
        name="databases"
        options={{
          title: "Databases",
          tabBarLabel: "Databases",
        }}
      />
      <Tabs.Screen
        name="analytics"
        options={{
          title: "Analytics",
          tabBarLabel: "Analytics",
        }}
      />
      <Tabs.Screen
        name="ai/insights"
        options={{
          title: "Insights",
          tabBarLabel: "Insights",
        }}
      />
      <Tabs.Screen
        name="ai/recommendations"
        options={{
          title: "Recommendations",
          tabBarLabel: "Recommendations",
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: "Search",
          tabBarLabel: "Search",
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          href: null, // hide from tab bar — index just redirects
        }}
      />
    </Tabs>
  );
}
