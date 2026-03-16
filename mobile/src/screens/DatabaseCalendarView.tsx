/*
KOROBOS — Mobile Calendar View (Stub)

Placeholder for Calendar view on mobile.
Sprint 8 feature: Display records on a calendar by date property.
*/

import React, { useState } from "react";
import { View, Text, StyleSheet, ScrollView, Pressable } from "react-native";
import { Database, DatabaseRecord, RecordValue } from "../services/databaseApi";

interface Props {
  database: Database;
  records: DatabaseRecord[];
}

export function DatabaseCalendarView({ database, records }: Props) {
  const dateProps = database.properties.filter((p) => p.type === "date");
  const [currentMonth, setCurrentMonth] = useState(new Date());

  if (!dateProps.length) {
    return (
      <View style={styles.container}>
        <Text style={styles.notice}>
          📅 Create a "date" property to use Calendar view
        </Text>
      </View>
    );
  }

  const dateProp = dateProps[0];
  const recordsByDate = new Map<string, DatabaseRecord[]>();

  records.forEach((record) => {
    const dateValue = record.values.find(
      (v: RecordValue) => v.property_id === dateProp.id,
    )?.value;
    if (dateValue) {
      if (!recordsByDate.has(dateValue)) {
        recordsByDate.set(dateValue, []);
      }
      recordsByDate.get(dateValue)!.push(record);
    }
  });

  const monthStart = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth(),
    1,
  );
  const monthEnd = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth() + 1,
    0,
  );
  const days: (Date | null)[] = [];

  for (let i = 0; i < monthStart.getDay(); i++) {
    days.push(null);
  }

  for (let day = 1; day <= monthEnd.getDate(); day++) {
    days.push(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day),
    );
  }

  const handlePrevMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1),
    );
  };

  const handleNextMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1),
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={handlePrevMonth} style={styles.navButton}>
          <Text style={styles.navButtonText}>←</Text>
        </Pressable>
        <Text style={styles.monthTitle}>
          {currentMonth.toLocaleDateString("en-US", {
            month: "long",
            year: "numeric",
          })}
        </Text>
        <Pressable onPress={handleNextMonth} style={styles.navButton}>
          <Text style={styles.navButtonText}>→</Text>
        </Pressable>
      </View>

      <View style={styles.weekDays}>
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <Text key={day} style={styles.weekDay}>
            {day}
          </Text>
        ))}
      </View>

      <View style={styles.dates}>
        {days.map((date, index) => {
          if (!date) {
            return <View key={`empty-${index}`} style={styles.emptyDay} />;
          }

          const dateStr = date.toISOString().split("T")[0];
          const dayRecords = recordsByDate.get(dateStr) || [];

          return (
            <View key={dateStr} style={styles.day}>
              <Text style={styles.dayNumber}>{date.getDate()}</Text>
              <View style={styles.dayRecords}>
                {dayRecords.slice(0, 1).map((record) => (
                  <Text key={record.id} style={styles.dayRecord}>
                    {record.id.substring(0, 4)}
                  </Text>
                ))}
                {dayRecords.length > 1 && (
                  <Text style={styles.more}>+{dayRecords.length - 1}</Text>
                )}
              </View>
            </View>
          );
        })}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
    padding: 16,
  },
  notice: {
    fontSize: 14,
    color: "#999",
    textAlign: "center",
    marginTop: 20,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
    backgroundColor: "white",
    padding: 12,
    borderRadius: 8,
  },
  navButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#667eea",
    borderRadius: 6,
  },
  navButtonText: {
    fontSize: 16,
    color: "white",
    fontWeight: "600",
  },
  monthTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#333",
  },
  weekDays: {
    flexDirection: "row",
    marginBottom: 8,
  },
  weekDay: {
    flex: 1,
    textAlign: "center",
    fontSize: 12,
    fontWeight: "700",
    color: "#667eea",
    paddingVertical: 8,
  },
  dates: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  emptyDay: {
    width: "14.28%",
    aspectRatio: 1,
  },
  day: {
    width: "14.28%",
    aspectRatio: 1,
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#eee",
    padding: 4,
    justifyContent: "flex-start",
  },
  dayNumber: {
    fontSize: 11,
    fontWeight: "700",
    color: "#333",
  },
  dayRecords: {
    marginTop: 2,
  },
  dayRecord: {
    fontSize: 8,
    backgroundColor: "#667eea",
    color: "white",
    paddingHorizontal: 2,
    paddingVertical: 1,
    borderRadius: 2,
    overflow: "hidden",
  },
  more: {
    fontSize: 8,
    color: "#667eea",
    fontWeight: "600",
    marginTop: 1,
  },
});
