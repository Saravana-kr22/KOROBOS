/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Databases Page — List and manage structured databases
*/

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "./databases.module.css";

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
  database_id: string;
  name: string;
  type: string;
  options?: Record<string, unknown>;
  position: number;
  created_at: string;
}

interface CreateDatabaseForm {
  name: string;
  icon?: string;
  description?: string;
}

interface SearchResult {
  id: string;
  type: "note" | "record";
  title?: string;
  content?: string;
  database_id?: string;
  record_id?: string;
}

export default function DatabasesPage() {
  const [databases, setDatabases] = useState<Database[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CreateDatabaseForm>({
    name: "",
    icon: "",
    description: "",
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/api/v1/databases", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch databases");
      }

      const data = await response.json();
      setDatabases(data.databases || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDatabase = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await fetch("/api/v1/databases", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to create database");
      }

      setFormData({ name: "", icon: "", description: "" });
      setShowCreateForm(false);
      await fetchDatabases();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create database",
      );
    }
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);

    if (!query.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setIsSearching(true);
    try {
      // Search both notes and records indexes
      const [notesRes, recordsRes] = await Promise.allSettled([
        fetch(`${process.env.NEXT_PUBLIC_SEARCH_URL}/indexes/notes/search`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(process.env.NEXT_PUBLIC_SEARCH_API_KEY && {
              Authorization: `Bearer ${process.env.NEXT_PUBLIC_SEARCH_API_KEY}`,
            }),
          },
          body: JSON.stringify({
            q: query,
            limit: 10,
          }),
        }),
        fetch(`${process.env.NEXT_PUBLIC_SEARCH_URL}/indexes/records/search`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(process.env.NEXT_PUBLIC_SEARCH_API_KEY && {
              Authorization: `Bearer ${process.env.NEXT_PUBLIC_SEARCH_API_KEY}`,
            }),
          },
          body: JSON.stringify({
            q: query,
            limit: 10,
          }),
        }),
      ]);

      const results: SearchResult[] = [];

      if (notesRes.status === "fulfilled" && notesRes.value.ok) {
        const data = (await notesRes.value.json()) as Record<
          string,
          SearchResult[]
        >;
        (data.hits || []).forEach((hit: SearchResult) => {
          results.push({
            id: hit.id,
            type: "note",
            title: hit.title,
            content: hit.content?.substring(0, 100),
          });
        });
      }

      if (recordsRes.status === "fulfilled" && recordsRes.value.ok) {
        const data = (await recordsRes.value.json()) as Record<
          string,
          SearchResult[]
        >;
        (data.hits || []).forEach((hit: SearchResult) => {
          results.push({
            id: hit.id,
            type: "record",
            content: hit.content?.substring(0, 100),
            database_id: hit.database_id,
            record_id: hit.record_id,
          });
        });
      }

      setSearchResults(results);
      setShowSearchResults(true);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.container}>
          <p>Loading databases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>Databases</h1>
          <button
            className={styles.primaryButton}
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? "Cancel" : "+ New Database"}
          </button>
        </div>

        {/* Search Bar */}
        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder="Search notes & records..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className={styles.searchInput}
          />
          {isSearching && <span className={styles.searchSpinner}>⏳</span>}
        </div>

        {/* Search Results */}
        {showSearchResults && searchResults.length > 0 && (
          <div className={styles.searchResults}>
            <div className={styles.searchResultsHeader}>
              <h3>Search Results ({searchResults.length})</h3>
              <button
                className={styles.closeButton}
                onClick={() => setShowSearchResults(false)}
              >
                ✕
              </button>
            </div>
            <div className={styles.resultsList}>
              {searchResults.map((result) => (
                <SearchResultItem key={result.id} result={result} />
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className={styles.error}>
            <p>Error: {error}</p>
          </div>
        )}

        {showCreateForm && (
          <form onSubmit={handleCreateDatabase} className={styles.createForm}>
            <div className={styles.formGroup}>
              <label htmlFor="name">Database Name *</label>
              <input
                id="name"
                type="text"
                placeholder="e.g., Books, Projects, Recipes"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="icon">Icon (Emoji)</label>
              <input
                id="icon"
                type="text"
                placeholder="e.g., 📚, 🎯, 🍳"
                value={formData.icon || ""}
                onChange={(e) =>
                  setFormData({ ...formData, icon: e.target.value })
                }
                maxLength={2}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                placeholder="Describe what this database is for..."
                value={formData.description || ""}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
              />
            </div>

            <button type="submit" className={styles.primaryButton}>
              Create Database
            </button>
          </form>
        )}

        {databases.length === 0 ? (
          <div className={styles.empty}>
            <p>No databases yet. Create one to get started!</p>
          </div>
        ) : (
          <div className={styles.databaseGrid}>
            {databases.map((db) => (
              <DatabaseCard key={db.id} database={db} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SearchResultItem({ result }: { result: SearchResult }) {
  if (result.type === "note") {
    return (
      <Link href={`/notes/${result.id}`} className={styles.resultItem}>
        <span className={styles.resultType}>📝 Note</span>
        <div className={styles.resultContent}>
          <h4>{result.title || "Untitled"}</h4>
          <p>{result.content}</p>
        </div>
      </Link>
    );
  }

  return (
    <Link
      href={`/databases/${result.database_id}`}
      className={styles.resultItem}
    >
      <span className={styles.resultType}>📋 Record</span>
      <div className={styles.resultContent}>
        <h4>{result.record_id?.substring(0, 8)}...</h4>
        <p>{result.content || "No content"}</p>
      </div>
    </Link>
  );
}

function DatabaseCard({ database }: { database: Database }) {
  return (
    <Link href={`/databases/${database.id}`} className={styles.databaseCard}>
      <div className={styles.cardHeader}>
        <span className={styles.icon}>{database.icon || "📊"}</span>
        <h2>{database.name}</h2>
      </div>

      {database.description && (
        <p className={styles.description}>{database.description}</p>
      )}

      <div className={styles.cardFooter}>
        <span className={styles.propertyCount}>
          {database.properties.length} field
          {database.properties.length !== 1 ? "s" : ""}
        </span>
        <time className={styles.created}>
          {new Date(database.created_at).toLocaleDateString()}
        </time>
      </div>
    </Link>
  );
}
