/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Topics Screen — create, rename, and delete learning topics.
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import { learningApi } from "../services/learningApi";
import { Topic } from "../types/learning";

export default function TopicsScreen() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [newName, setNewName] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const loadTopics = useCallback(async () => {
    try {
      setError("");
      const data = await learningApi.listTopics();
      setTopics(data.topics || []);
    } catch {
      setError("Failed to load topics");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);
  useFocusEffect(
    useCallback(() => {
      loadTopics();
    }, [loadTopics]),
  );

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await learningApi.createTopic({ name: newName.trim() });
      setNewName("");
      setShowForm(false);
      await loadTopics();
    } catch {
      Alert.alert("Error", "Failed to create topic");
    }
  };

  const handleUpdate = async (topicId: string) => {
    if (!editName.trim()) return;
    try {
      await learningApi.updateTopic(topicId, { name: editName.trim() });
      setEditingId(null);
      setEditName("");
      await loadTopics();
    } catch {
      Alert.alert("Error", "Failed to update topic");
    }
  };

  const handleDelete = (topic: Topic) => {
    Alert.alert(
      "Delete Topic",
      `Delete "${topic.name}"? Sessions linked to it will not be deleted.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await learningApi.deleteTopic(topic.id);
              await loadTopics();
            } catch {
              Alert.alert("Error", "Failed to delete topic");
            }
          },
        },
      ],
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      {/* Create form */}
      {showForm && (
        <View style={styles.createForm}>
          <TextInput
            style={styles.input}
            placeholder="Topic name"
            value={newName}
            onChangeText={setNewName}
            autoFocus
            onSubmitEditing={handleCreate}
            returnKeyType="done"
          />
          <View style={styles.row}>
            <TouchableOpacity
              style={[styles.btn, styles.btnSuccess]}
              onPress={handleCreate}
            >
              <Text style={styles.btnText}>Create</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.btnSecondary]}
              onPress={() => {
                setShowForm(false);
                setNewName("");
              }}
            >
              <Text style={styles.btnTextDark}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <FlatList
        data={topics}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadTopics();
            }}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No topics yet.</Text>
            <Text style={styles.emptySubtext}>
              Create topics to organise your learning sessions.
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.topicRow}>
            {editingId === item.id ? (
              <>
                <TextInput
                  style={[styles.input, styles.inlineInput]}
                  value={editName}
                  onChangeText={setEditName}
                  autoFocus
                  onSubmitEditing={() => handleUpdate(item.id)}
                  returnKeyType="done"
                />
                <TouchableOpacity
                  style={[styles.iconBtn, styles.iconBtnSave]}
                  onPress={() => handleUpdate(item.id)}
                >
                  <Text style={styles.iconBtnText}>✓</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.iconBtn, styles.iconBtnCancel]}
                  onPress={() => {
                    setEditingId(null);
                    setEditName("");
                  }}
                >
                  <Text style={styles.iconBtnText}>✕</Text>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <View style={styles.topicInfo}>
                  <Text style={styles.topicName}>{item.name}</Text>
                  <Text style={styles.topicDate}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </Text>
                </View>
                <TouchableOpacity
                  style={[styles.iconBtn, styles.iconBtnEdit]}
                  onPress={() => {
                    setEditingId(item.id);
                    setEditName(item.name);
                  }}
                >
                  <Text style={styles.iconBtnTextDark}>Edit</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.iconBtn, styles.iconBtnDelete]}
                  onPress={() => handleDelete(item)}
                >
                  <Text style={styles.iconBtnText}>Del</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        )}
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => {
          setShowForm(!showForm);
          setEditingId(null);
        }}
      >
        <Text style={styles.fabText}>{showForm ? "✕" : "+"}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  errorText: { color: "#dc3545", padding: 16, fontSize: 14 },

  createForm: {
    backgroundColor: "#fff",
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    padding: 10,
    marginBottom: 8,
    fontSize: 15,
    backgroundColor: "#fafafa",
  },
  inlineInput: { flex: 1, marginBottom: 0, marginRight: 6 },
  row: { flexDirection: "row", gap: 8 },

  topicRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    marginHorizontal: 10,
    marginVertical: 4,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#eee",
  },
  topicInfo: { flex: 1 },
  topicName: { fontSize: 15, fontWeight: "600", color: "#333" },
  topicDate: { fontSize: 12, color: "#999", marginTop: 2 },

  btn: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 6,
    alignItems: "center",
  },
  btnSuccess: { backgroundColor: "#28a745" },
  btnSecondary: { backgroundColor: "#e9ecef" },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 14 },
  btnTextDark: { color: "#333", fontWeight: "600", fontSize: 14 },

  iconBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 6,
  },
  iconBtnSave: { backgroundColor: "#28a745" },
  iconBtnCancel: { backgroundColor: "#6c757d" },
  iconBtnEdit: { backgroundColor: "#e9ecef" },
  iconBtnDelete: { backgroundColor: "#dc3545" },
  iconBtnText: { color: "#fff", fontSize: 13, fontWeight: "600" },
  iconBtnTextDark: { color: "#333", fontSize: 13, fontWeight: "600" },

  emptyContainer: { padding: 40, alignItems: "center" },
  emptyText: { fontSize: 16, color: "#666", marginBottom: 6 },
  emptySubtext: { fontSize: 13, color: "#999", textAlign: "center" },

  fab: {
    position: "absolute",
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#007bff",
    justifyContent: "center",
    alignItems: "center",
    elevation: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3,
  },
  fabText: { color: "#fff", fontSize: 26, fontWeight: "bold" },
});
