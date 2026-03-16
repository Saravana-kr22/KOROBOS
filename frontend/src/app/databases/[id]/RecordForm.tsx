/*
KOROBOS — Database Record Form

Form component for creating/editing database records.
Supports all property types with appropriate input controls.
*/

"use client";

import React, { useState } from "react";
import styles from "./record-form.module.css";

interface Property {
  id: string;
  name: string;
  type: string;
  options?: Record<string, unknown>;
}

interface RecordFormProps {
  properties: Property[];
  initialValues?: Record<string, string>;
  onSubmit: (values: Record<string, string>) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function RecordForm({
  properties,
  initialValues = {},
  onSubmit,
  onCancel,
  isLoading = false,
}: RecordFormProps) {
  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (propertyId: string, value: string) => {
    setValues((prev) => ({ ...prev, [propertyId]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await onSubmit(values);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save record");
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.fields}>
        {properties.map((property) => (
          <div key={property.id} className={styles.field}>
            <label htmlFor={property.id}>{property.name}</label>
            {renderInput(property, values[property.id] || "", (val) =>
              handleChange(property.id, val),
            )}
          </div>
        ))}
      </div>

      <div className={styles.actions}>
        <button
          type="submit"
          className={styles.submitButton}
          disabled={isLoading}
        >
          {isLoading ? "Saving..." : "Save Record"}
        </button>
        <button
          type="button"
          className={styles.cancelButton}
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function renderInput(
  property: Property,
  value: string,
  onChange: (value: string) => void,
): React.ReactNode {
  const commonProps = {
    id: property.id,
    value,
    onChange: (
      e: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => onChange(e.target.value),
    disabled: false,
  };

  switch (property.type) {
    case "text":
      return (
        <textarea
          {...commonProps}
          placeholder={`Enter ${property.name}`}
          className={styles.textarea}
        />
      );

    case "number":
      return (
        <input
          {...commonProps}
          type="number"
          placeholder={`Enter ${property.name}`}
          className={styles.input}
        />
      );

    case "boolean":
      return (
        <select {...commonProps} className={styles.select}>
          <option value="">-- Select --</option>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      );

    case "date":
      return <input {...commonProps} type="date" className={styles.input} />;

    case "select":
      const choices = (property.options?.choices as string[]) || [];
      return (
        <select {...commonProps} className={styles.select}>
          <option value="">-- Select --</option>
          {choices.map((choice) => (
            <option key={choice} value={choice}>
              {choice}
            </option>
          ))}
        </select>
      );

    case "multi_select":
      const multiChoices = (property.options?.choices as string[]) || [];
      return (
        <select
          {...commonProps}
          multiple
          value={value ? value.split(",") : []}
          onChange={(e) => {
            const selected = Array.from(
              e.target.selectedOptions,
              (opt) => opt.value,
            );
            onChange(selected.join(","));
          }}
          className={styles.select}
        >
          {multiChoices.map((choice) => (
            <option key={choice} value={choice}>
              {choice}
            </option>
          ))}
        </select>
      );

    default:
      return (
        <input
          {...commonProps}
          type="text"
          placeholder={`Enter ${property.name}`}
          className={styles.input}
        />
      );
  }
}
