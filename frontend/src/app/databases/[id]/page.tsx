/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Database Detail Page — View and manage records in a database
*/

"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { RecordForm } from "./RecordForm";
import { KanbanView } from "./KanbanView";
import { CalendarView } from "./CalendarView";
import styles from "./database-detail.module.css";

interface Database {
  id: string;
  name: string;
  icon?: string;
  description?: string;
  properties: Property[];
  created_at: string;
  updated_at: string;
}

interface Property {
  id: string;
  name: string;
  type: string;
  options?: Record<string, unknown>;
  position: number;
}

interface DatabaseRecord {
  id: string;
  database_id: string;
  values: RecordValue[];
  created_at: string;
  updated_at: string;
}

interface RecordValue {
  property_id: string;
  value?: string;
}

interface RecordListResponse {
  records: DatabaseRecord[];
  total: number;
  page: number;
  limit: number;
}

export default function DatabaseDetailPage() {
  const params = useParams();
  const databaseId = params.id as string;

  const [database, setDatabase] = useState<Database | null>(null);
  const [records, setRecords] = useState<DatabaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRecord, setEditingRecord] = useState<DatabaseRecord | null>(
    null,
  );
  const [formLoading, setFormLoading] = useState(false);
  const [filterPropertyId, setFilterPropertyId] = useState<string>("");
  const [filterValue, setFilterValue] = useState<string>("");
  const [sortPropertyId, setSortPropertyId] = useState<string>("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [viewMode, setViewMode] = useState<"table" | "kanban" | "calendar">(
    "table",
  );

  const fetchDatabase = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/databases/${databaseId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch database");
      }

      const data = await response.json();
      setDatabase(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  }, [databaseId]);

  const fetchRecords = useCallback(async () => {
    try {
      setLoading(true);
      const url = new URL(
        `/api/v1/databases/${databaseId}/records`,
        window.location.origin,
      );
      url.searchParams.set("page", "1");
      url.searchParams.set("limit", "50");

      if (filterPropertyId && filterValue) {
        url.searchParams.set("filter_property_id", filterPropertyId);
        url.searchParams.set("filter_value", filterValue);
        url.searchParams.set("filter_operator", "eq");
      }

      if (sortPropertyId) {
        url.searchParams.set("sort_property_id", sortPropertyId);
        url.searchParams.set("sort_direction", sortDirection);
      }

      const response = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch records");
      }

      const data: RecordListResponse = await response.json();
      setRecords(data.records || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }, [
    databaseId,
    filterPropertyId,
    filterValue,
    sortPropertyId,
    sortDirection,
  ]);

  useEffect(() => {
    if (databaseId) {
      fetchDatabase();
    }
  }, [databaseId, fetchDatabase]);

  useEffect(() => {
    if (databaseId) {
      fetchRecords();
    }
  }, [databaseId, fetchRecords]);

  const handleCreateRecord = async (values: Record<string, string>) => {
    try {
      setFormLoading(true);
      const response = await fetch(`/api/v1/databases/${databaseId}/records`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
        body: JSON.stringify({ values }),
      });

      if (!response.ok) {
        throw new Error("Failed to create record");
      }

      setShowCreateForm(false);
      await fetchRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create record");
    } finally {
      setFormLoading(false);
    }
  };

  const handleUpdateRecord = async (values: Record<string, string>) => {
    if (!editingRecord) return;

    try {
      setFormLoading(true);
      const response = await fetch(`/api/v1/records/${editingRecord.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
        body: JSON.stringify({ values }),
      });

      if (!response.ok) {
        throw new Error("Failed to update record");
      }

      setEditingRecord(null);
      await fetchRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update record");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteRecord = async (recordId: string) => {
    if (!confirm("Are you sure you want to delete this record?")) return;

    try {
      const response = await fetch(`/api/v1/records/${recordId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete record");
      }

      await fetchRecords();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete record");
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <p>Loading database...</p>
      </div>
    );
  }

  if (!database) {
    return (
      <div className={styles.page}>
        <p>Database not found.</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.titleBlock}>
            <span className={styles.icon}>{database.icon || "📊"}</span>
            <div>
              <h1>{database.name}</h1>
              {database.description && (
                <p className={styles.description}>{database.description}</p>
              )}
            </div>
          </div>
          <Link href="/databases" className={styles.backButton}>
            ← Back to Databases
          </Link>
        </div>

        {error && (
          <div className={styles.error}>
            <p>Error: {error}</p>
          </div>
        )}

        <div className={styles.content}>
          <div className={styles.sidebar}>
            <h2>Fields ({database.properties.length})</h2>
            {database.properties.length === 0 ? (
              <p className={styles.empty}>No fields yet</p>
            ) : (
              <ul className={styles.propertyList}>
                {database.properties.map((prop) => (
                  <li key={prop.id} className={styles.propertyItem}>
                    <span className={styles.propertyName}>{prop.name}</span>
                    <span className={styles.propertyType}>{prop.type}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className={styles.main}>
            <div className={styles.mainHeader}>
              <h2>Records ({records.length})</h2>
              <button
                onClick={() => setShowCreateForm(true)}
                className={styles.createButton}
              >
                + New Record
              </button>
            </div>

            {showCreateForm && (
              <div className={styles.formSection}>
                <h3>Create New Record</h3>
                <RecordForm
                  properties={database.properties}
                  onSubmit={handleCreateRecord}
                  onCancel={() => setShowCreateForm(false)}
                  isLoading={formLoading}
                />
              </div>
            )}

            {editingRecord && (
              <div className={styles.formSection}>
                <h3>Edit Record</h3>
                <RecordForm
                  properties={database.properties}
                  initialValues={Object.fromEntries(
                    editingRecord.values.map((v) => [
                      v.property_id,
                      v.value || "",
                    ]),
                  )}
                  onSubmit={handleUpdateRecord}
                  onCancel={() => setEditingRecord(null)}
                  isLoading={formLoading}
                />
              </div>
            )}

            {/* View Mode Tabs */}
            <div className={styles.viewModeTabs}>
              <button
                onClick={() => setViewMode("table")}
                className={viewMode === "table" ? styles.tabActive : styles.tab}
              >
                📋 Table
              </button>
              <button
                onClick={() => setViewMode("kanban")}
                className={
                  viewMode === "kanban" ? styles.tabActive : styles.tab
                }
              >
                📊 Kanban
              </button>
              <button
                onClick={() => setViewMode("calendar")}
                className={
                  viewMode === "calendar" ? styles.tabActive : styles.tab
                }
              >
                📅 Calendar
              </button>
            </div>

            <div className={styles.filterSection}>
              <div className={styles.filterGroup}>
                <label htmlFor="filter-property">Filter by:</label>
                <select
                  id="filter-property"
                  value={filterPropertyId}
                  onChange={(e) => {
                    setFilterPropertyId(e.target.value);
                    setFilterValue("");
                  }}
                  className={styles.filterInput}
                >
                  <option value="">— None —</option>
                  {database.properties.map((prop) => (
                    <option key={prop.id} value={prop.id}>
                      {prop.name}
                    </option>
                  ))}
                </select>
              </div>

              {filterPropertyId && (
                <div className={styles.filterGroup}>
                  <label htmlFor="filter-value">Value:</label>
                  <input
                    id="filter-value"
                    type="text"
                    value={filterValue}
                    onChange={(e) => setFilterValue(e.target.value)}
                    placeholder="Enter value to filter..."
                    className={styles.filterInput}
                  />
                </div>
              )}

              <div className={styles.filterGroup}>
                <label htmlFor="sort-property">Sort by:</label>
                <select
                  id="sort-property"
                  value={sortPropertyId}
                  onChange={(e) => setSortPropertyId(e.target.value)}
                  className={styles.filterInput}
                >
                  <option value="">— None —</option>
                  <option value="_created">Created Date</option>
                  {database.properties.map((prop) => (
                    <option key={prop.id} value={prop.id}>
                      {prop.name}
                    </option>
                  ))}
                </select>
              </div>

              {sortPropertyId && (
                <div className={styles.filterGroup}>
                  <label htmlFor="sort-direction">Direction:</label>
                  <select
                    id="sort-direction"
                    value={sortDirection}
                    onChange={(e) =>
                      setSortDirection(e.target.value as "asc" | "desc")
                    }
                    className={styles.filterInput}
                  >
                    <option value="asc">Ascending</option>
                    <option value="desc">Descending</option>
                  </select>
                </div>
              )}
            </div>

            {records.length === 0 ? (
              <p className={styles.empty}>No records yet. Create one!</p>
            ) : viewMode === "table" ? (
              <div className={styles.recordsTable}>
                <div className={styles.tableHeader}>
                  <div className={styles.tableCell}>ID</div>
                  {database.properties.map((prop) => (
                    <div key={prop.id} className={styles.tableCell}>
                      {prop.name}
                    </div>
                  ))}
                  <div className={styles.tableCell}>Created</div>
                  <div className={styles.tableCell}>Actions</div>
                </div>

                {records.map((record) => (
                  <div key={record.id} className={styles.tableRow}>
                    <div className={styles.tableCell}>
                      <code className={styles.recordId}>
                        {record.id.substring(0, 8)}...
                      </code>
                    </div>
                    {database.properties.map((prop) => {
                      const value = record.values.find(
                        (v) => v.property_id === prop.id,
                      )?.value;
                      return (
                        <div key={prop.id} className={styles.tableCell}>
                          {value || "—"}
                        </div>
                      );
                    })}
                    <div className={styles.tableCell}>
                      <time>
                        {new Date(record.created_at).toLocaleDateString()}
                      </time>
                    </div>
                    <div className={styles.tableCell}>
                      <div className={styles.actions}>
                        <button
                          onClick={() => setEditingRecord(record)}
                          className={styles.editButton}
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteRecord(record.id)}
                          className={styles.deleteButton}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : viewMode === "kanban" ? (
              <KanbanView records={records} properties={database.properties} />
            ) : (
              <CalendarView
                records={records}
                properties={database.properties}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
