/**
 * KOROBOS — Habit detail page (dynamic route).
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React from "react";
import HabitDetailScreen from "../../src/screens/HabitDetailScreen";

export default function HabitDetailPage() {
  const router = useRouter();
  const { habitId } = useLocalSearchParams<{ habitId: string }>();
  const navigation = {
    navigate: (name: string, params?: any) =>
      router.push(`/habits/${params?.habitId}`),
    goBack: () => router.back(),
    setOptions: (_opts: any) => {},
  };
  const route = { params: { habitId } } as any;
  return <HabitDetailScreen navigation={navigation} route={route} />;
}
