/**
 * KOROBOS — Database detail page (dynamic route).
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React from "react";
import { DatabaseDetailScreen } from "../../../src/screens/DatabaseDetailScreen";

export default function DatabaseDetailPage() {
  const router = useRouter();
  const { databaseId } = useLocalSearchParams<{ databaseId: string }>();
  const navigation = {
    navigate: (name: string, params?: any) => {
      if (name === "DatabaseKanban")
        router.push(`/databases/${databaseId}/kanban`);
      else if (name === "DatabaseCalendar")
        router.push(`/databases/${databaseId}/calendar`);
    },
    goBack: () => router.back(),
    setOptions: (_opts: any) => {},
  };
  const route = { params: { databaseId } } as any;
  return <DatabaseDetailScreen navigation={navigation as any} route={route} />;
}
