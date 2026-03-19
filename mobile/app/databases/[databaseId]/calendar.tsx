/**
 * KOROBOS — Database calendar view page.
 */

import { useLocalSearchParams, useRouter } from "expo-router";
import React from "react";
import DatabaseCalendarView from "../../../src/screens/DatabaseCalendarView";

export default function CalendarPage() {
  const router = useRouter();
  const { databaseId } = useLocalSearchParams<{ databaseId: string }>();
  const navigation = {
    goBack: () => router.back(),
    setOptions: (_opts: any) => {},
  };
  const route = { params: { databaseId } } as any;
  return <DatabaseCalendarView navigation={navigation} route={route} />;
}
