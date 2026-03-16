/*
KOROBOS — Kanban View (Stub)

Placeholder implementation for Kanban view.
Sprint 8 enhancement: Organize records by select/multi_select property columns.
*/

import React from "react";
import styles from "./kanban-view.module.css";

interface Property {
  id: string;
  name: string;
  type: string;
  options?: Record<string, unknown>;
}

interface DatabaseRecord {
  id: string;
  values: Array<{ property_id: string; value?: string }>;
}

interface KanbanViewProps {
  records: DatabaseRecord[];
  properties: Property[];
}

export function KanbanView({ records, properties }: KanbanViewProps) {
  const selectProps = properties.filter((p) => p.type === "select");

  if (!selectProps.length) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <p>Create a &quot;select&quot; property to use Kanban view</p>
        </div>
      </div>
    );
  }

  const selectProp = selectProps[0];
  const choices = (selectProp.options?.choices as string[]) || [];
  const columnMap = new Map<string, DatabaseRecord[]>();

  choices.forEach((choice) => {
    columnMap.set(choice, []);
  });

  records.forEach((record) => {
    const value = record.values.find((v) => v.property_id === selectProp.id)
      ?.value;
    if (value && columnMap.has(value)) {
      columnMap.get(value)!.push(record);
    }
  });

  return (
    <div className={styles.container}>
      <div className={styles.notice}>
        📋 Kanban view grouping by &quot;{selectProp.name}&quot; (Sprint 8
        feature)
      </div>

      <div className={styles.board}>
        {choices.map((choice) => (
          <div key={choice} className={styles.column}>
            <div className={styles.columnHeader}>
              <h3>{choice}</h3>
              <span className={styles.count}>
                {columnMap.get(choice)?.length || 0}
              </span>
            </div>
            <div className={styles.cards}>
              {columnMap.get(choice)?.map((record) => (
                <div key={record.id} className={styles.card}>
                  <p className={styles.cardId}>
                    {record.id.substring(0, 8)}...
                  </p>
                  <p className={styles.cardNote}>
                    {record.values[0]?.value || "—"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
