/**
 * KOROBOS — Habits list page.
 */

import { useRouter } from "expo-router";
import React from "react";
import HabitsListScreen from "../../src/screens/HabitsListScreen";

export default function HabitsPage() {
  const router = useRouter();
  const navigation = {
    navigate: (name: string, params?: any) => {
      if (name === "HabitDetail") {
        router.push(`/habits/${params?.habitId}`);
      }
    },
    goBack: () => router.back(),
  };
  return <HabitsListScreen navigation={navigation} />;
}
