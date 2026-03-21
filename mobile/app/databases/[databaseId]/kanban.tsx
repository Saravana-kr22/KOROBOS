/**
 * KOROBOS — Database kanban view page.
 */

import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { DatabaseKanbanView } from "../../../src/screens/DatabaseKanbanView";
import {
  Database,
  DatabaseRecord,
  databaseApi,
} from "../../../src/services/databaseApi";

export default function KanbanPage() {
  const { databaseId } = useLocalSearchParams<{ databaseId: string }>();
  const [database, setDatabase] = useState<Database | null>(null);
  const [records, setRecords] = useState<DatabaseRecord[]>([]);

  useEffect(() => {
    if (databaseId) {
      databaseApi.getDatabase(databaseId).then(setDatabase);
      databaseApi
        .listRecords(databaseId, { limit: 100 })
        .then((r) => setRecords(r.records));
    }
  }, [databaseId]);

  if (!database) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator />
      </View>
    );
  }

  return <DatabaseKanbanView database={database} records={records} />;
}
