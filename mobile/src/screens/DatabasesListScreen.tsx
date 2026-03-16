/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Databases List Screen — React Native mobile view
*/

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { databaseApi, Database, Property } from "../services/databaseApi";

type RootStackParamList = {
  DatabasesList: undefined;
  DatabaseDetail: { databaseId: string };
};

type Props = NativeStackScreenProps<RootStackParamList, "DatabasesList">;

export function DatabasesListScreen({ navigation }: Props) {
  const [databases, setDatabases] = useState<Database[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await databaseApi.listDatabases(1, 50);
      setDatabases(response.databases || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetchDatabases();
    } finally {
      setRefreshing(false);
    }
  }, []);

  const renderDatabase = ({ item }: { item: Database }) => (
    <TouchableOpacity
      style={styles.databaseCard}
      onPress={() =>
        navigation.navigate("DatabaseDetail", { databaseId: item.id })
      }
    >
      <View style={styles.cardContent}>
        <Text style={styles.cardIcon}>{item.icon || "📊"}</Text>
        <View style={styles.cardInfo}>
          <Text style={styles.cardTitle}>{item.name}</Text>
          {item.description && (
            <Text style={styles.cardDescription}>{item.description}</Text>
          )}
          <Text style={styles.cardMeta}>
            {item.properties.length} field
            {item.properties.length !== 1 ? "s" : ""}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>My Databases</Text>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {databases.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>
            No databases yet. Create one to get started!
          </Text>
        </View>
      ) : (
        <FlatList
          data={databases}
          keyExtractor={(item) => item.id}
          renderItem={renderDatabase}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor="#667eea"
            />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  header: {
    fontSize: 28,
    fontWeight: "bold",
    padding: 16,
    paddingTop: 20,
    color: "#333",
  },
  errorBanner: {
    backgroundColor: "#fee",
    borderLeftWidth: 4,
    borderLeftColor: "#c33",
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 6,
  },
  errorText: {
    color: "#c33",
    fontSize: 14,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  databaseCard: {
    backgroundColor: "white",
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: "#667eea",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
  },
  cardContent: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
  },
  cardIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  cardInfo: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 13,
    color: "#666",
    marginBottom: 6,
  },
  cardMeta: {
    fontSize: 12,
    color: "#999",
  },
  empty: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 16,
  },
  emptyText: {
    fontSize: 16,
    color: "#999",
    textAlign: "center",
  },
});
