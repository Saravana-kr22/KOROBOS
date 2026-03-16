/*
KOROBOS — Mobile Kanban View (Stub)

Placeholder for Kanban view on mobile.
Sprint 8 feature: Organize records by select property.
*/

import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import {
  Database,
  DatabaseRecord,
  Property,
  RecordValue,
} from "../services/databaseApi";

interface Props {
  database: Database;
  records: DatabaseRecord[];
}

export function DatabaseKanbanView({ database, records }: Props) {
  const selectProps = database.properties.filter((p) => p.type === "select");

  if (!selectProps.length) {
    return (
      <View style={styles.container}>
        <Text style={styles.notice}>
          📋 Create a "select" property to use Kanban view
        </Text>
      </View>
    );
  }

  const selectProp = selectProps[0];
  const choices = (selectProp.options?.choices as string[]) || [];
  const columnMap = new Map<string, DatabaseRecord[]>();

  choices.forEach((choice) => {
    columnMap.set(choice, []);
  });

  records.forEach((record) => {
    const value = record.values.find(
      (v: RecordValue) => v.property_id === selectProp.id,
    )?.value;
    if (value && columnMap.has(value)) {
      columnMap.get(value)!.push(record);
    }
  });

  return (
    <ScrollView horizontal style={styles.container}>
      <View style={styles.board}>
        {choices.map((choice) => (
          <View key={choice} style={styles.column}>
            <View style={styles.columnHeader}>
              <Text style={styles.columnTitle}>{choice}</Text>
              <Text style={styles.count}>
                {columnMap.get(choice)?.length || 0}
              </Text>
            </View>
            <ScrollView style={styles.cards}>
              {columnMap.get(choice)?.map((record) => (
                <View key={record.id} style={styles.card}>
                  <Text style={styles.cardId}>
                    {record.id.substring(0, 6)}...
                  </Text>
                </View>
              ))}
            </ScrollView>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  notice: {
    fontSize: 14,
    color: "#999",
    textAlign: "center",
    marginTop: 20,
  },
  board: {
    flexDirection: "row",
    gap: 12,
  },
  column: {
    width: 280,
    backgroundColor: "white",
    borderRadius: 8,
    overflow: "hidden",
    borderLeftWidth: 4,
    borderLeftColor: "#667eea",
  },
  columnHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    backgroundColor: "#f9f9f9",
  },
  columnTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#333",
  },
  count: {
    fontSize: 12,
    backgroundColor: "#667eea",
    color: "white",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    fontWeight: "600",
  },
  cards: {
    padding: 8,
    maxHeight: 500,
  },
  card: {
    backgroundColor: "#f0f0f0",
    borderRadius: 6,
    padding: 10,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: "#667eea",
  },
  cardId: {
    fontSize: 12,
    color: "#667eea",
    fontFamily: "monospace",
    fontWeight: "600",
  },
});
