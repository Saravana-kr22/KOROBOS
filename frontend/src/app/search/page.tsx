/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Page — unified search across all domains with filtering.
*/

"use client";

import { useState, useCallback, useRef } from "react";
import styles from "./search.module.css";
import { searchApi, SearchResult } from "./searchApi";

const TYPE_LABELS: Record<string, string> = {
  note: "Note",
  habit: "Habit",
  learning: "Learning",
  record: "Record",
  meal: "Meal",
  workout: "Workout",
};

const TYPE_ICONS: Record<string, string> = {
  note: "📝",
  habit: "✅",
  learning: "📚",
  record: "🗄️",
  meal: "🍽️",
  workout: "💪",
};

const TYPE_COLORS: Record<string, string> = {
  note: "#4b6ff5",
  habit: "#28a745",
  learning: "#17a2b8",
  record: "#6c757d",
  meal: "#fd7e14",
  workout: "#e83e8c",
};

interface SearchState {
  query: string;
  results: SearchResult[];
  total: number;
  loading: boolean;
  error: string | null;
  selectedType: string;
  dateFrom: string;
  dateTo: string;
  tags: string;
  page: number;
  limit: number;
  suggestions: string[];
  showSuggestions: boolean;
  inputValue: string;
}

export default function SearchPage() {
  const [state, setState] = useState<SearchState>({
    query: "",
    results: [],
    total: 0,
    loading: false,
    error: null,
    selectedType: "",
    dateFrom: "",
    dateTo: "",
    tags: "",
    page: 1,
    limit: 20,
    suggestions: [],
    showSuggestions: false,
    inputValue: "",
  });

  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const suggestTimeoutRef = useRef<NodeJS.Timeout>();

  // Debounced suggest
  const handleInputChange = useCallback(
    (value: string) => {
      setState((prev) => ({ ...prev, inputValue: value }));

      if (suggestTimeoutRef.current) {
        clearTimeout(suggestTimeoutRef.current);
      }

      if (value.length < 2) {
        setState((prev) => ({
          ...prev,
          suggestions: [],
          showSuggestions: false,
        }));
        return;
      }

      suggestTimeoutRef.current = setTimeout(async () => {
        if (!token) return;
        try {
          const response = await searchApi.suggest(token, value);
          setState((prev) => ({
            ...prev,
            suggestions: response.suggestions.slice(0, 5),
            showSuggestions: true,
          }));
        } catch (err) {
          console.error("Suggest error:", err);
        }
      }, 300);
    },
    [token],
  );

  const performSearch = useCallback(
    async (query: string, page: number = 1) => {
      if (!query.trim() || !token) return;

      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const offset = (page - 1) * state.limit;

        const response = await searchApi.searchAdvanced(token, query, {
          type: state.selectedType || undefined,
          date_from: state.dateFrom || undefined,
          date_to: state.dateTo || undefined,
          tags: state.tags
            ? state.tags.split(",").map((t) => t.trim())
            : undefined,
          limit: state.limit,
          offset,
        });

        setState((prev) => ({
          ...prev,
          results: response.results,
          total: response.total,
          error: null,
          page,
          showSuggestions: false,
        }));
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Search failed";
        setState((prev) => ({
          ...prev,
          error: errorMsg,
          results: [],
        }));
      } finally {
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    [
      token,
      state.selectedType,
      state.dateFrom,
      state.dateTo,
      state.tags,
      state.limit,
    ],
  );

  const handleSearch = useCallback(() => {
    setState((prev) => ({ ...prev, query: prev.inputValue }));
    performSearch(state.inputValue, 1);
  }, [state.inputValue, performSearch]);

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      setState((prev) => ({
        ...prev,
        inputValue: suggestion,
        showSuggestions: false,
      }));
      performSearch(suggestion, 1);
    },
    [performSearch],
  );

  const handleFilterChange = useCallback(
    (type: string, value: string) => {
      setState((prev) => {
        const updated = { ...prev, [type]: value };
        if (updated.query) {
          performSearch(updated.query, 1);
        }
        return updated;
      });
    },
    [performSearch],
  );

  const handleTypeFilterChange = useCallback(
    (type: string) => {
      setState((prev) => ({ ...prev, selectedType: type }));
      if (state.query) {
        performSearch(state.query, 1);
      }
    },
    [state.query, performSearch],
  );

  const handlePreviousPage = useCallback(() => {
    if (state.page > 1) {
      performSearch(state.query, state.page - 1);
    }
  }, [state.page, state.query, performSearch]);

  const handleNextPage = useCallback(() => {
    const maxPage = Math.ceil(state.total / state.limit);
    if (state.page < maxPage) {
      performSearch(state.query, state.page + 1);
    }
  }, [state.page, state.total, state.limit, state.query, performSearch]);

  const maxPage = Math.ceil(state.total / state.limit);
  const startResult = (state.page - 1) * state.limit + 1;
  const endResult = Math.min(state.page * state.limit, state.total);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Unified Search</h1>
        <p>
          Search across all your notes, habits, learning, records, meals, and
          workouts
        </p>
      </header>

      <div className={styles.searchArea}>
        <div className={styles.searchBox}>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search for anything..."
            value={state.inputValue}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch();
              }
            }}
          />
          <button
            className={styles.searchButton}
            onClick={handleSearch}
            disabled={state.loading}
          >
            {state.loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Suggestions dropdown */}
        {state.showSuggestions && state.suggestions.length > 0 && (
          <div className={styles.suggestionsDropdown}>
            {state.suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                className={styles.suggestionItem}
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <span className={styles.suggestionIcon}>🔍</span>
                <span>{suggestion}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={styles.content}>
        {/* Sidebar filters */}
        <aside className={styles.sidebar}>
          <div className={styles.filterSection}>
            <h3 className={styles.filterTitle}>Type</h3>
            <div className={styles.typeFilters}>
              <label className={styles.typeLabel}>
                <input
                  type="radio"
                  name="type"
                  value=""
                  checked={state.selectedType === ""}
                  onChange={(e) => handleTypeFilterChange(e.target.value)}
                />
                All Types
              </label>
              {Object.entries(TYPE_LABELS).map(([key, label]) => (
                <label key={key} className={styles.typeLabel}>
                  <input
                    type="radio"
                    name="type"
                    value={key}
                    checked={state.selectedType === key}
                    onChange={(e) => handleTypeFilterChange(e.target.value)}
                  />
                  {TYPE_ICONS[key]} {label}
                </label>
              ))}
            </div>
          </div>

          <div className={styles.filterSection}>
            <h3 className={styles.filterTitle}>Date Range</h3>
            <input
              type="date"
              className={styles.filterInput}
              value={state.dateFrom}
              onChange={(e) => handleFilterChange("dateFrom", e.target.value)}
            />
            <input
              type="date"
              className={styles.filterInput}
              value={state.dateTo}
              onChange={(e) => handleFilterChange("dateTo", e.target.value)}
            />
          </div>

          <div className={styles.filterSection}>
            <h3 className={styles.filterTitle}>Tags</h3>
            <input
              type="text"
              className={styles.filterInput}
              placeholder="Comma-separated tags"
              value={state.tags}
              onChange={(e) => handleFilterChange("tags", e.target.value)}
            />
          </div>
        </aside>

        {/* Results area */}
        <main className={styles.results}>
          {state.error && (
            <div className={styles.errorMessage}>
              <span>❌ {state.error}</span>
            </div>
          )}

          {state.query === "" ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🔍</div>
              <h2>Start Searching</h2>
              <p>
                Enter a search query above to find notes, habits, learning,
                records, meals, and workouts across all your data.
              </p>
            </div>
          ) : state.loading && state.results.length === 0 ? (
            <div className={styles.loadingState}>
              <div className={styles.spinner}></div>
              <p>Searching...</p>
            </div>
          ) : state.results.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📭</div>
              <h2>No Results Found</h2>
              <p>Try adjusting your search query or filters.</p>
            </div>
          ) : (
            <>
              <div className={styles.resultsHeader}>
                <span className={styles.resultCount}>
                  {state.total === 0
                    ? "No results"
                    : `${startResult}–${endResult} of ${state.total} results`}
                </span>
              </div>

              <div className={styles.resultsList}>
                {state.results.map((result) => (
                  <div key={result.id} className={styles.resultCard}>
                    <div className={styles.resultCardHeader}>
                      <span
                        className={styles.resultTypeBadge}
                        style={{
                          backgroundColor: TYPE_COLORS[result.type] || "#999",
                        }}
                      >
                        {TYPE_ICONS[result.type] || "?"}{" "}
                        {TYPE_LABELS[result.type] || result.type}
                      </span>
                      {result.created_at && (
                        <span className={styles.resultDate}>
                          {new Date(result.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <h3 className={styles.resultTitle}>{result.title}</h3>
                    <p className={styles.resultSnippet}>{result.snippet}</p>
                    {result.score && (
                      <span className={styles.resultScore}>
                        Relevance: {Math.round(result.score * 100)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {maxPage > 1 && (
                <div className={styles.pagination}>
                  <button
                    className={styles.paginationButton}
                    onClick={handlePreviousPage}
                    disabled={state.page === 1}
                  >
                    ← Previous
                  </button>
                  <span className={styles.pageInfo}>
                    Page {state.page} of {maxPage}
                  </span>
                  <button
                    className={styles.paginationButton}
                    onClick={handleNextPage}
                    disabled={state.page === maxPage}
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
