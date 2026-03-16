/*
KOROBOS — Calendar View (Stub)

Placeholder implementation for Calendar view.
Sprint 8 enhancement: Display records on a calendar by date property.
*/

import React, { useState } from "react";
import styles from "./calendar-view.module.css";

interface Property {
  id: string;
  name: string;
  type: string;
}

interface DatabaseRecord {
  id: string;
  values: Array<{ property_id: string; value?: string }>;
}

interface CalendarViewProps {
  records: DatabaseRecord[];
  properties: Property[];
}

export function CalendarView({ records, properties }: CalendarViewProps) {
  const dateProps = properties.filter((p) => p.type === "date");
  const [currentMonth, setCurrentMonth] = useState(new Date());

  if (!dateProps.length) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <p>Create a &quot;date&quot; property to use Calendar view</p>
        </div>
      </div>
    );
  }

  const dateProp = dateProps[0];
  const recordsByDate = new Map<string, DatabaseRecord[]>();

  records.forEach((record) => {
    const dateValue = record.values.find((v) => v.property_id === dateProp.id)
      ?.value;
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
  const days = [];

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
    <div className={styles.container}>
      <div className={styles.notice}>
        📅 Calendar view by &quot;{dateProp.name}&quot; (Sprint 8 feature)
      </div>

      <div className={styles.calendar}>
        <div className={styles.header}>
          <button onClick={handlePrevMonth}>←</button>
          <h3>
            {currentMonth.toLocaleDateString("en-US", {
              month: "long",
              year: "numeric",
            })}
          </h3>
          <button onClick={handleNextMonth}>→</button>
        </div>

        <div className={styles.weekDays}>
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
            <div key={day} className={styles.weekDay}>
              {day}
            </div>
          ))}
        </div>

        <div className={styles.dates}>
          {days.map((date, index) => {
            if (!date) {
              return <div key={`empty-${index}`} className={styles.emptyDay} />;
            }

            const dateStr = date.toISOString().split("T")[0];
            const dayRecords = recordsByDate.get(dateStr) || [];

            return (
              <div key={dateStr} className={styles.day}>
                <div className={styles.dayNumber}>{date.getDate()}</div>
                <div className={styles.dayRecords}>
                  {dayRecords.slice(0, 2).map((record) => (
                    <div key={record.id} className={styles.dayRecord}>
                      {record.id.substring(0, 4)}
                    </div>
                  ))}
                  {dayRecords.length > 2 && (
                    <div className={styles.more}>+{dayRecords.length - 2}</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
