/**
 * KOROBOS — Databases list page.
 */

import { useRouter } from "expo-router";
import React from "react";
import { DatabasesListScreen } from "../../src/screens/DatabasesListScreen";

export default function DatabasesPage() {
  const router = useRouter();
  const navigation = {
    navigate: (name: string, params?: any) => {
      if (name === "DatabaseDetail") {
        router.push(`/databases/${params?.databaseId}`);
      }
    },
    goBack: () => router.back(),
  };
  return (
    <DatabasesListScreen
      navigation={navigation as any}
      route={{ params: {} } as any}
    />
  );
}
