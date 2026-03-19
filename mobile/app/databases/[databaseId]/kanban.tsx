/**
 * KOROBOS — Database kanban view page.
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React from "react";
import DatabaseKanbanView from "../../../src/screens/DatabaseKanbanView";

export default function KanbanPage() {
  const router = useRouter();
  const { databaseId } = useLocalSearchParams<{ databaseId: string }>();
  const navigation = {
    goBack: () => router.back(),
    setOptions: (_opts: any) => {},
  };
  const route = { params: { databaseId } } as any;
  return <DatabaseKanbanView navigation={navigation} route={route} />;
}
