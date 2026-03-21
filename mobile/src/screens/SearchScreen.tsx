/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Search Screen — unified search across all domains.
 */

import React, {
  useState,
  useCallback,
  useEffect,
  useRef,
  useFocusEffect,
} from "react";
import {
  SafeAreaView,
  ScrollView,
  FlatList,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect as useNavFocusEffect } from "@react-navigation/native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  searchApi,
  SearchResult,
  SuggestResponse,
} from "../services/searchApi";

const TYPE_ICONS: Record<string, string> = {
  note: "📝",
  habit: "✅",
  learning: "📚",
  record: "🗄️",
  meal: "🍽️",
  workout: "💪",
  topic: "🏷️",
};

const FILTER_OPTIONS = [
  { label: "All", value: null },
  { label: "Notes", value: "note" },
  { label: "Habits", value: "habit" },
  { label: "Learning", value: "learning" },
  { label: "Records", value: "record" },
  { label: "Meals", value: "meal" },
  { label: "Workouts", value: "workout" },
];

interface SearchState {
  query: string;
  results: SearchResult[];
  suggestions: string[];
  showSuggestions: boolean;
  activeType: string | null;
  dateFrom: string;
  dateTo: string;
  tags: string;
  showAdvancedFilters: boolean;
  isStale: boolean;
  loading: boolean;
  error: string;
  page: number;
  total: number;
}

export default function SearchScreen() {
  const [state, setState] = useState<SearchState>({
    query: "",
    results: [],
    suggestions: [],
    showSuggestions: false,
    activeType: null,
    dateFrom: "",
    dateTo: "",
    tags: "",
    showAdvancedFilters: false,
    isStale: false,
    loading: false,
    error: "",
    page: 1,
    total: 0,
  });

  const suggestTimeoutRef = useRef<NodeJS.Timeout>();

  // Debounced suggest
  const handleInputChange = useCallback((text: string) => {
    setState((prev) => ({ ...prev, query: text }));

    // Clear previous timeout
    if (suggestTimeoutRef.current) {
      clearTimeout(suggestTimeoutRef.current);
    }

    if (text.length < 2) {
      setState((prev) => ({
        ...prev,
        suggestions: [],
        showSuggestions: false,
      }));
      return;
    }

    suggestTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await searchApi.suggest(text);
        setState((prev) => ({
          ...prev,
          suggestions: response.suggestions,
          showSuggestions: true,
        }));
      } catch (err) {
        console.error("Suggest error:", err);
      }
    }, 300);
  }, []);

  const performSearch = useCallback(
    async (
      query: string,
      type: string | null = state.activeType,
      offset: number = 0,
    ) => {
      if (!query.trim()) {
        setState((prev) => ({ ...prev, results: [], total: 0 }));
        return;
      }

      setState((prev) => ({ ...prev, loading: true, error: "" }));

      const cacheKey = `korobos:search_cache:${query}:${type}:${offset}`;
      const hasAdvancedFilters =
        !!state.dateFrom || !!state.dateTo || !!state.tags.trim();

      try {
        let response;

        if (hasAdvancedFilters) {
          // Use advanced search when filters are present
          response = await searchApi.searchAdvanced(query, {
            type: type || undefined,
            date_from: state.dateFrom || undefined,
            date_to: state.dateTo || undefined,
            tags: state.tags
              ? state.tags
                  .split(",")
                  .map((t) => t.trim())
                  .filter(Boolean)
              : undefined,
            limit: 20,
            offset,
          });
        } else {
          // Use basic search
          response = await searchApi.search(
            query,
            type || undefined,
            20,
            offset,
          );
        }

        // Cache successful search results
        try {
          await AsyncStorage.setItem(cacheKey, JSON.stringify(response));
        } catch (cacheErr) {
          console.warn("Failed to cache search results:", cacheErr);
        }

        setState((prev) => ({
          ...prev,
          results:
            offset === 0
              ? response.results
              : [...prev.results, ...response.results],
          total: response.total,
          error: "",
          page: Math.floor(offset / 20) + 1,
          isStale: false,
        }));
      } catch (err) {
        // Try to load from cache on failure
        try {
          const cached = await AsyncStorage.getItem(cacheKey);
          if (cached) {
            const response = JSON.parse(cached);
            setState((prev) => ({
              ...prev,
              results:
                offset === 0
                  ? response.results
                  : [...prev.results, ...response.results],
              total: response.total,
              error: "",
              page: Math.floor(offset / 20) + 1,
              isStale: true,
            }));
            return;
          }
        } catch (cacheReadErr) {
          console.warn("Failed to read search cache:", cacheReadErr);
        }

        const errorMsg = err instanceof Error ? err.message : "Search failed";
        setState((prev) => ({ ...prev, error: errorMsg }));
      } finally {
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    [state.activeType, state.dateFrom, state.dateTo, state.tags],
  );

  const handleSearch = useCallback(() => {
    setState((prev) => ({ ...prev, showSuggestions: false }));
    performSearch(state.query, state.activeType, 0);
  }, [state.query, state.activeType, performSearch]);

  const handleSuggestionTap = useCallback(
    (suggestion: string) => {
      setState((prev) => ({
        ...prev,
        query: suggestion,
        showSuggestions: false,
      }));
      // Execute search with the suggestion
      performSearch(suggestion, state.activeType, 0);
    },
    [state.activeType, performSearch],
  );

  const handleFilterTap = useCallback(
    (type: string | null) => {
      setState((prev) => ({ ...prev, activeType: type, page: 1 }));
      performSearch(state.query, type, 0);
    },
    [state.query, performSearch],
  );

  const handleLoadMore = useCallback(() => {
    if (state.results.length < state.total && !state.loading) {
      performSearch(state.query, state.activeType, state.results.length);
    }
  }, [
    state.results.length,
    state.total,
    state.loading,
    state.query,
    state.activeType,
    performSearch,
  ]);

  const handleClear = useCallback(() => {
    setState((prev) => ({
      ...prev,
      query: "",
      results: [],
      suggestions: [],
      showSuggestions: false,
    }));
  }, []);

  const handleClearFilters = useCallback(() => {
    setState((prev) => ({
      ...prev,
      dateFrom: "",
      dateTo: "",
      tags: "",
    }));
    performSearch(state.query, state.activeType, 0);
  }, [state.query, state.activeType, performSearch]);

  useNavFocusEffect(
    useCallback(() => {
      // Refresh on tab focus
      if (state.query.trim()) {
        performSearch(state.query, state.activeType, 0);
      }
    }, [state.query, state.activeType, performSearch]),
  );

  const renderSearchResultCard = ({ item }: { item: SearchResult }) => (
    <View style={styles.resultCard}>
      <View style={styles.resultHeader}>
        <Text style={styles.resultIcon}>{TYPE_ICONS[item.type] || "❓"}</Text>
        <View style={styles.resultMeta}>
          <Text style={styles.resultTitle} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.resultType}>{item.type}</Text>
        </View>
      </View>
      <Text style={styles.resultSnippet} numberOfLines={2}>
        {item.snippet}
      </Text>
      {item.score && (
        <Text style={styles.resultScore}>
          Relevance: {Math.round(item.score * 100)}%
        </Text>
      )}
    </View>
  );

  const renderSuggestionItem = ({ item }: { item: string }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => handleSuggestionTap(item)}
    >
      <Text style={styles.suggestionText}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header with search bar */}
      <View style={styles.searchBarContainer}>
        <View style={styles.searchInputWrapper}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search across all domains..."
            placeholderTextColor="#999"
            value={state.query}
            onChangeText={handleInputChange}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {state.query.length > 0 && (
            <TouchableOpacity onPress={handleClear} style={styles.clearButton}>
              <Text style={styles.clearButtonText}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() =>
            setState((prev) => ({
              ...prev,
              showAdvancedFilters: !prev.showAdvancedFilters,
            }))
          }
        >
          <Text style={styles.filterButtonText}>⚙️</Text>
          {(state.dateFrom || state.dateTo || state.tags) && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>●</Text>
            </View>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.searchButton}
          onPress={handleSearch}
          disabled={state.loading}
        >
          <Text style={styles.searchButtonText}>
            {state.loading ? "..." : "Search"}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Suggestions dropdown */}
      {state.showSuggestions && state.suggestions.length > 0 && (
        <View style={styles.suggestionsContainer}>
          <FlatList
            data={state.suggestions}
            keyExtractor={(item, idx) => `${item}-${idx}`}
            renderItem={renderSuggestionItem}
            scrollEnabled={false}
          />
        </View>
      )}

      {/* Stale data banner */}
      {state.isStale && (
        <View style={styles.staleBanner}>
          <Text style={styles.staleBannerText}>⚠️ Showing cached results</Text>
        </View>
      )}

      {/* Advanced filters panel */}
      {state.showAdvancedFilters && (
        <View style={styles.advancedFiltersPanel}>
          <View style={styles.filterGroup}>
            <Text style={styles.filterLabel}>From Date (YYYY-MM-DD)</Text>
            <TextInput
              style={styles.filterInput}
              placeholder="2026-01-01"
              value={state.dateFrom}
              onChangeText={(text) =>
                setState((prev) => ({ ...prev, dateFrom: text }))
              }
            />
          </View>
          <View style={styles.filterGroup}>
            <Text style={styles.filterLabel}>To Date (YYYY-MM-DD)</Text>
            <TextInput
              style={styles.filterInput}
              placeholder="2026-12-31"
              value={state.dateTo}
              onChangeText={(text) =>
                setState((prev) => ({ ...prev, dateTo: text }))
              }
            />
          </View>
          <View style={styles.filterGroup}>
            <Text style={styles.filterLabel}>Tags (comma-separated)</Text>
            <TextInput
              style={styles.filterInput}
              placeholder="python, ai, learning"
              value={state.tags}
              onChangeText={(text) =>
                setState((prev) => ({ ...prev, tags: text }))
              }
            />
          </View>
          <TouchableOpacity
            style={styles.clearFiltersButton}
            onPress={handleClearFilters}
          >
            <Text style={styles.clearFiltersText}>Clear Filters</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Filter chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterChipsContainer}
        contentContainerStyle={styles.filterChipsContent}
      >
        {FILTER_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.value || "all"}
            style={[
              styles.filterChip,
              state.activeType === option.value && styles.filterChipActive,
            ]}
            onPress={() => handleFilterTap(option.value)}
          >
            <Text
              style={[
                styles.filterChipText,
                state.activeType === option.value &&
                  styles.filterChipTextActive,
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Results or empty state */}
      {state.error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error: {state.error}</Text>
        </View>
      ) : state.query.trim() === "" ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>🔍</Text>
          <Text style={styles.emptyTitle}>Start Searching</Text>
          <Text style={styles.emptyMessage}>
            Enter a keyword above to search across notes, habits, learning,
            records, and health logs.
          </Text>
        </View>
      ) : state.results.length === 0 && !state.loading ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No results</Text>
          <Text style={styles.emptyMessage}>
            Try a different search term or adjust your filters.
          </Text>
        </View>
      ) : (
        <FlatList
          data={state.results}
          keyExtractor={(item) => item.id}
          renderItem={renderSearchResultCard}
          contentContainerStyle={styles.resultsList}
          ListFooterComponent={
            state.results.length < state.total && !state.loading ? (
              <TouchableOpacity
                style={styles.loadMoreButton}
                onPress={handleLoadMore}
              >
                <Text style={styles.loadMoreText}>
                  Load More ({state.results.length} of {state.total})
                </Text>
              </TouchableOpacity>
            ) : state.loading ? (
              <ActivityIndicator
                size="large"
                color="#007bff"
                style={styles.loader}
              />
            ) : null
          }
          refreshControl={
            <RefreshControl
              refreshing={state.loading}
              onRefresh={handleSearch}
              tintColor="#007bff"
            />
          }
        />
      )}

      {/* Loading indicator (top of screen) */}
      {state.loading && state.results.length === 0 && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#007bff" />
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  searchBarContainer: {
    flexDirection: "row",
    gap: 8,
    padding: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#dee2e6",
    alignItems: "center",
  },
  searchInputWrapper: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f8f9fa",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 16,
    color: "#333",
  },
  clearButton: {
    padding: 8,
  },
  clearButtonText: {
    fontSize: 18,
    color: "#999",
  },
  searchButton: {
    backgroundColor: "#007bff",
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: "center",
    minHeight: 44,
  },
  searchButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  suggestionsContainer: {
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#dee2e6",
    maxHeight: 200,
  },
  suggestionItem: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  suggestionText: {
    fontSize: 14,
    color: "#333",
  },
  filterChipsContainer: {
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#dee2e6",
  },
  filterChipsContent: {
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#f0f0f0",
    borderWidth: 1,
    borderColor: "#dee2e6",
  },
  filterChipActive: {
    backgroundColor: "#007bff",
    borderColor: "#0056b3",
  },
  filterChipText: {
    fontSize: 13,
    color: "#666",
    fontWeight: "500",
  },
  filterChipTextActive: {
    color: "#fff",
  },
  resultsList: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
  resultCard: {
    backgroundColor: "#fff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#dee2e6",
    padding: 12,
    marginBottom: 4,
  },
  resultHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 8,
    gap: 10,
  },
  resultIcon: {
    fontSize: 24,
    marginTop: 2,
  },
  resultMeta: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 4,
  },
  resultType: {
    fontSize: 12,
    color: "#999",
    textTransform: "capitalize",
  },
  resultSnippet: {
    fontSize: 14,
    color: "#666",
    lineHeight: 20,
    marginBottom: 6,
  },
  resultScore: {
    fontSize: 12,
    color: "#007bff",
  },
  loadMoreButton: {
    paddingVertical: 12,
    alignItems: "center",
  },
  loadMoreText: {
    color: "#007bff",
    fontSize: 14,
    fontWeight: "600",
  },
  loader: {
    paddingVertical: 20,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  emptyText: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  emptyMessage: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    lineHeight: 20,
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  errorText: {
    fontSize: 14,
    color: "#dc3545",
    textAlign: "center",
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.2)",
    justifyContent: "center",
    alignItems: "center",
  },
  filterButton: {
    position: "relative",
    justifyContent: "center",
    alignItems: "center",
    width: 44,
    height: 44,
  },
  filterButtonText: {
    fontSize: 18,
  },
  filterBadge: {
    position: "absolute",
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#dc3545",
    justifyContent: "center",
    alignItems: "center",
  },
  filterBadgeText: {
    color: "#fff",
    fontSize: 6,
  },
  staleBanner: {
    backgroundColor: "#fff3cd",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#ffc107",
  },
  staleBannerText: {
    color: "#856404",
    fontSize: 14,
    fontWeight: "500",
  },
  advancedFiltersPanel: {
    backgroundColor: "#f8f9fa",
    borderBottomWidth: 1,
    borderBottomColor: "#dee2e6",
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 12,
  },
  filterGroup: {
    gap: 6,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#333",
    textTransform: "uppercase",
  },
  filterInput: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 14,
    color: "#333",
  },
  clearFiltersButton: {
    alignSelf: "flex-end",
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  clearFiltersText: {
    color: "#007bff",
    fontSize: 13,
    fontWeight: "600",
    textDecorationLine: "underline",
  },
});
