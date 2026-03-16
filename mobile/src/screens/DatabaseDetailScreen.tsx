/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Database Detail Screen — View and manage records in a database
*/

import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  Modal,
  StyleSheet,
  ActivityIndicator,
  FlatList,
  RefreshControl,
  Pressable,
  TextInput,
  ScrollView,
  Alert,
  Switch,
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import {
  databaseApi,
  Database,
  DatabaseRecord,
  Property,
} from "../services/databaseApi";
import { DatabaseKanbanView } from "./DatabaseKanbanView";
import { DatabaseCalendarView } from "./DatabaseCalendarView";

type RootStackParamList = {
  DatabaseDetail: { databaseId: string };
};

type Props = NativeStackScreenProps<RootStackParamList, "DatabaseDetail">;

interface FilterState {
  propertyId: string;
  value: string;
}

type RecordValues = Record<string, string>;

export function DatabaseDetailScreen({ route, navigation }: Props) {
  const { databaseId } = route.params;

  const [database, setDatabase] = useState<Database | null>(null);
  const [records, setRecords] = useState<DatabaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<DatabaseRecord | null>(
    null,
  );
  const [recordValues, setRecordValues] = useState<RecordValues>({});
  const [isSaving, setIsSaving] = useState(false);
  const [filter, setFilter] = useState<FilterState>({
    propertyId: "",
    value: "",
  });
  const [viewMode, setViewMode] = useState<"table" | "kanban" | "calendar">(
    "table",
  );

  useEffect(() => {
    if (databaseId) {
      fetchDatabase();
    }
  }, [databaseId]);

  useEffect(() => {
    if (databaseId) {
      fetchRecords();
    }
  }, [databaseId, filter]);

  useEffect(() => {
    if (database) {
      navigation.setOptions({
        title: `${database.icon || "📊"} ${database.name}`,
        headerRight: () => (
          <Pressable
            onPress={() => setShowCreateModal(true)}
            style={styles.headerBtn}
          >
            <Text style={styles.headerBtnText}>+ New</Text>
          </Pressable>
        ),
      });
    }
  }, [database, navigation]);

  const fetchDatabase = async () => {
    try {
      const data = await databaseApi.getDatabase(databaseId);
      setDatabase(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const options: { [key: string]: number | string } = { limit: 50 };
      if (filter.propertyId && filter.value) {
        options.filter_property_id = filter.propertyId;
        options.filter_value = filter.value;
        options.filter_operator = "eq";
      }
      const response = await databaseApi.listRecords(databaseId, options);
      setRecords(response.records || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([fetchDatabase(), fetchRecords()]);
    } finally {
      setRefreshing(false);
    }
  }, [filter, databaseId]);

  const handleCreateRecord = async () => {
    if (!database || !Object.keys(recordValues).length) {
      Alert.alert("Validation", "Please fill in at least one field");
      return;
    }

    try {
      setIsSaving(true);
      await databaseApi.createRecord(databaseId, { values: recordValues });
      setShowCreateModal(false);
      setRecordValues({});
      await fetchRecords();
      Alert.alert("Success", "Record created successfully");
    } catch (err) {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to create record",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateRecord = async () => {
    if (!editingRecord) return;

    try {
      setIsSaving(true);
      await databaseApi.updateRecord(editingRecord.id, {
        values: recordValues,
      });
      setEditingRecord(null);
      setRecordValues({});
      await fetchRecords();
      Alert.alert("Success", "Record updated successfully");
    } catch (err) {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to update record",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteRecord = async (recordId: string) => {
    Alert.alert("Delete Record", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await databaseApi.deleteRecord(recordId);
            await fetchRecords();
            Alert.alert("Success", "Record deleted successfully");
          } catch (err) {
            Alert.alert(
              "Error",
              err instanceof Error ? err.message : "Failed to delete record",
            );
          }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    );
  }

  if (!database) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>Database not found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <View style={styles.filterBar}>
        <Pressable
          onPress={() => setFilter({ propertyId: "", value: "" })}
          style={
            filter.propertyId
              ? [styles.filterBtn, styles.filterBtnActive]
              : styles.filterBtn
          }
        >
          <Text style={styles.filterBtnText}>
            {filter.propertyId
              ? `Filter: ${
                  database.properties.find((p) => p.id === filter.propertyId)
                    ?.name || ""
                }`
              : "Filter"}
          </Text>
        </Pressable>
      </View>

      {/* View Mode Tabs */}
      <View style={styles.viewModeTabs}>
        <Pressable
          onPress={() => setViewMode("table")}
          style={[styles.tab, viewMode === "table" && styles.tabActive]}
        >
          <Text
            style={[
              styles.tabText,
              viewMode === "table" && styles.tabTextActive,
            ]}
          >
            📋 Table
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setViewMode("kanban")}
          style={[styles.tab, viewMode === "kanban" && styles.tabActive]}
        >
          <Text
            style={[
              styles.tabText,
              viewMode === "kanban" && styles.tabTextActive,
            ]}
          >
            📊 Kanban
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setViewMode("calendar")}
          style={[styles.tab, viewMode === "calendar" && styles.tabActive]}
        >
          <Text
            style={[
              styles.tabText,
              viewMode === "calendar" && styles.tabTextActive,
            ]}
          >
            📅 Calendar
          </Text>
        </Pressable>
      </View>

      {viewMode === "table" ? (
        <FlatList
          data={records}
          keyExtractor={(item) => item.id}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor="#667eea"
            />
          }
          ListHeaderComponent={
            <View style={styles.fieldsSection}>
              <Text style={styles.sectionTitle}>
                Fields ({database.properties.length})
              </Text>
              {database.properties.map((prop) => (
                <View key={prop.id} style={styles.fieldItem}>
                  <Text style={styles.fieldName}>{prop.name}</Text>
                  <Text style={styles.fieldType}>{prop.type}</Text>
                </View>
              ))}
            </View>
          }
          ListHeaderComponentStyle={styles.listHeader}
          renderItem={({ item: record }) => (
            <View style={styles.recordItem}>
              <View style={styles.recordHeader}>
                <View>
                  <Text style={styles.recordId} numberOfLines={1}>
                    {record.id.substring(0, 8)}...
                  </Text>
                  <Text style={styles.recordDate}>
                    {new Date(record.created_at).toLocaleDateString()}
                  </Text>
                </View>
                <View style={styles.recordActions}>
                  <Pressable
                    onPress={() => {
                      setEditingRecord(record);
                      const vals: RecordValues = {};
                      record.values.forEach((v) => {
                        if (v.value) vals[v.property_id] = v.value;
                      });
                      setRecordValues(vals);
                      setShowCreateModal(true);
                    }}
                    style={styles.actionBtn}
                  >
                    <Text style={styles.actionBtnText}>Edit</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => handleDeleteRecord(record.id)}
                    style={[styles.actionBtn, styles.deleteBtn]}
                  >
                    <Text style={[styles.actionBtnText, styles.deleteBtnText]}>
                      Delete
                    </Text>
                  </Pressable>
                </View>
              </View>
              <View style={styles.recordValues}>
                {database.properties.map((prop) => {
                  const value = record.values.find(
                    (v) => v.property_id === prop.id,
                  )?.value;
                  return (
                    <View key={prop.id} style={styles.recordValue}>
                      <Text style={styles.valueName}>{prop.name}</Text>
                      <Text style={styles.valueText} numberOfLines={2}>
                        {value || "—"}
                      </Text>
                    </View>
                  );
                })}
              </View>
            </View>
          )}
          ListEmptyComponent={
            !loading && (
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>No records yet</Text>
              </View>
            )
          }
          contentContainerStyle={styles.listContent}
        />
      ) : viewMode === "kanban" ? (
        <DatabaseKanbanView database={database} records={records} />
      ) : (
        <DatabaseCalendarView database={database} records={records} />
      )}

      {/* Create/Edit Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        onRequestClose={() => {
          setShowCreateModal(false);
          setEditingRecord(null);
          setRecordValues({});
        }}
      >
        <ScrollView
          style={styles.modalContainer}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingRecord ? "Edit Record" : "Create Record"}
            </Text>
          </View>

          {database.properties.map((prop) => (
            <View key={prop.id} style={styles.formField}>
              <Text style={styles.fieldLabel}>{prop.name}</Text>
              {renderPropertyInput(
                prop,
                recordValues[prop.id] || "",
                (value: string) => {
                  setRecordValues((prev: RecordValues) => ({
                    ...prev,
                    [prop.id]: value,
                  }));
                },
              )}
            </View>
          ))}

          <View style={styles.modalActions}>
            <Pressable
              onPress={editingRecord ? handleUpdateRecord : handleCreateRecord}
              disabled={isSaving}
              style={[styles.submitBtn, isSaving && styles.submitBtnDisabled]}
            >
              <Text style={styles.submitBtnText}>
                {isSaving ? "Saving..." : editingRecord ? "Update" : "Create"}
              </Text>
            </Pressable>
            <Pressable
              onPress={() => {
                setShowCreateModal(false);
                setEditingRecord(null);
                setRecordValues({});
              }}
              style={styles.cancelBtn}
            >
              <Text style={styles.cancelBtnText}>Cancel</Text>
            </Pressable>
          </View>
        </ScrollView>
      </Modal>

      {/* Filter Modal */}
      <Modal
        visible={filter.propertyId !== ""}
        animationType="fade"
        transparent
        onRequestClose={() => setFilter({ propertyId: "", value: "" })}
      >
        <Pressable
          style={styles.filterOverlay}
          onPress={() => setFilter({ propertyId: "", value: "" })}
        >
          <View style={styles.filterModal}>
            <Text style={styles.filterModalTitle}>Filter Records</Text>
            <Picker
              selectedValue={filter.propertyId}
              onValueChange={(value: string) =>
                setFilter((prev) => ({ ...prev, propertyId: value }))
              }
              style={styles.picker}
            >
              <Picker.Item label="All Records" value="" />
              {database.properties.map((prop) => (
                <Picker.Item key={prop.id} label={prop.name} value={prop.id} />
              ))}
            </Picker>
            {filter.propertyId && (
              <>
                <Text style={styles.filterValueLabel}>Value:</Text>
                <TextInput
                  style={styles.filterInput}
                  placeholder="Enter filter value..."
                  value={filter.value}
                  onChangeText={(value) =>
                    setFilter((prev) => ({ ...prev, value }))
                  }
                />
              </>
            )}
            <Pressable
              onPress={() => setFilter({ propertyId: "", value: "" })}
              style={styles.filterCloseBtn}
            >
              <Text style={styles.filterCloseBtnText}>Done</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

function renderPropertyInput(
  prop: Property,
  value: string,
  onChange: (value: string) => void,
) {
  switch (prop.type) {
    case "text":
      return (
        <TextInput
          style={styles.input}
          placeholder={`Enter ${prop.name}`}
          value={value}
          onChangeText={onChange}
          multiline
        />
      );
    case "number":
      return (
        <TextInput
          style={styles.input}
          placeholder={`Enter ${prop.name}`}
          value={value}
          onChangeText={onChange}
          keyboardType="numeric"
        />
      );
    case "boolean":
      return (
        <View style={styles.booleanInput}>
          <Switch
            value={value === "true"}
            onValueChange={(v) => onChange(v ? "true" : "false")}
          />
          <Text style={styles.booleanText}>
            {value === "true" ? "Yes" : "No"}
          </Text>
        </View>
      );
    case "date":
      return (
        <TextInput
          style={styles.input}
          placeholder="YYYY-MM-DD"
          value={value}
          onChangeText={onChange}
        />
      );
    case "select":
      const choices = (prop.options?.choices as string[]) || [];
      return (
        <Picker
          selectedValue={value}
          onValueChange={onChange}
          style={styles.picker}
        >
          <Picker.Item label="-- Select --" value="" />
          {choices.map((choice) => (
            <Picker.Item key={choice} label={choice} value={choice} />
          ))}
        </Picker>
      );
    case "multi_select":
      return (
        <TextInput
          style={styles.input}
          placeholder="Enter values separated by commas"
          value={value}
          onChangeText={onChange}
          multiline
        />
      );
    default:
      return (
        <TextInput
          style={styles.input}
          placeholder={`Enter ${prop.name}`}
          value={value}
          onChangeText={onChange}
        />
      );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  errorBanner: {
    backgroundColor: "#fee",
    borderLeftWidth: 4,
    borderLeftColor: "#c33",
    padding: 12,
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 6,
  },
  errorText: {
    color: "#c33",
    fontSize: 14,
  },
  error: {
    color: "#666",
    fontSize: 16,
    textAlign: "center",
    marginTop: 20,
  },
  filterBar: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: "white",
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  filterBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#f0f0f0",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#ddd",
  },
  filterBtnActive: {
    backgroundColor: "#e8e8ff",
    borderColor: "#667eea",
  },
  filterBtnText: {
    fontSize: 13,
    color: "#666",
    fontWeight: "600",
  },
  viewModeTabs: {
    flexDirection: "row",
    backgroundColor: "white",
    borderBottomWidth: 2,
    borderBottomColor: "#eee",
    paddingHorizontal: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: 3,
    borderBottomColor: "transparent",
    alignItems: "center",
  },
  tabActive: {
    borderBottomColor: "#667eea",
  },
  tabText: {
    fontSize: 12,
    color: "#999",
    fontWeight: "600",
  },
  tabTextActive: {
    color: "#667eea",
  },
  listHeader: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  fieldsSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 8,
  },
  fieldItem: {
    backgroundColor: "white",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    marginBottom: 8,
    borderRadius: 6,
    borderLeftWidth: 3,
    borderLeftColor: "#667eea",
  },
  fieldName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  fieldType: {
    fontSize: 12,
    color: "white",
    backgroundColor: "#667eea",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  recordItem: {
    backgroundColor: "white",
    padding: 12,
    marginBottom: 8,
    borderRadius: 6,
  },
  recordHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  recordId: {
    fontSize: 12,
    fontFamily: "monospace",
    color: "#667eea",
    marginBottom: 4,
  },
  recordDate: {
    fontSize: 12,
    color: "#999",
  },
  recordActions: {
    flexDirection: "row",
    gap: 6,
  },
  actionBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: "#667eea",
    borderRadius: 4,
  },
  deleteBtn: {
    backgroundColor: "#fee",
  },
  actionBtnText: {
    fontSize: 12,
    color: "white",
    fontWeight: "600",
  },
  deleteBtnText: {
    color: "#c33",
  },
  recordValues: {
    gap: 8,
  },
  recordValue: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  valueName: {
    fontSize: 13,
    fontWeight: "600",
    color: "#666",
    flex: 1,
  },
  valueText: {
    fontSize: 13,
    color: "#333",
    flex: 1,
    marginLeft: 8,
    textAlign: "right",
  },
  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 32,
  },
  emptyText: {
    fontSize: 16,
    color: "#999",
  },
  headerBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 16,
  },
  headerBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#667eea",
  },
  modalContainer: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  modalHeader: {
    backgroundColor: "white",
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#333",
  },
  formField: {
    backgroundColor: "white",
    marginHorizontal: 16,
    marginTop: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#666",
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 4,
    padding: 8,
    fontSize: 14,
    minHeight: 40,
  },
  booleanInput: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  booleanText: {
    fontSize: 14,
    color: "#333",
  },
  picker: {
    height: 50,
  },
  modalActions: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 16,
    marginBottom: 16,
  },
  submitBtn: {
    flex: 1,
    backgroundColor: "#667eea",
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: "center",
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    fontSize: 14,
    fontWeight: "bold",
    color: "white",
  },
  cancelBtn: {
    flex: 1,
    backgroundColor: "#eee",
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: "center",
  },
  cancelBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#666",
  },
  filterOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  filterModal: {
    backgroundColor: "white",
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  filterModalTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 12,
  },
  filterValueLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#666",
    marginTop: 12,
    marginBottom: 6,
  },
  filterInput: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 4,
    padding: 8,
    fontSize: 14,
    marginBottom: 12,
  },
  filterCloseBtn: {
    backgroundColor: "#667eea",
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 12,
  },
  filterCloseBtnText: {
    fontSize: 14,
    fontWeight: "bold",
    color: "white",
  },
});
