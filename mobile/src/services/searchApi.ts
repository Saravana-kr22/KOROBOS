/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * API client for the Search Service (mobile/React Native).
 * Wraps the singleton apiClient to provide typed methods.
 */

import { apiClient } from "./apiClient";

/**
 * Single search result from any domain.
 */
export interface SearchResult {
  id: string;
  type: "note" | "habit" | "learning" | "record" | "meal" | "workout";
  title: string;
  snippet: string;
  user_id: string;
  score?: number;
  created_at?: string;
}

/**
 * Response from a search query.
 */
export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  limit: number;
  offset: number;
  processing_time_ms: number;
}

/**
 * Response from a suggest/autocomplete query.
 */
export interface SuggestResponse {
  query: string;
  suggestions: string[];
}

/**
 * Advanced search filter parameters.
 */
export interface AdvancedSearchParams {
  type?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

/**
 * Search API client for the unified search service.
 */
export const searchApi = {
  /**
   * Execute a basic search across all domains.
   *
   * @param q - Search query string
   * @param type - Optional type filter (note, habit, learning, record, meal, workout)
   * @param limit - Results per page (default 20, max 50)
   * @param offset - Pagination offset (default 0)
   */
  async search(
    q: string,
    type?: string,
    limit: number = 20,
    offset: number = 0,
  ): Promise<SearchResponse> {
    const params: Record<string, string> = {
      q,
      limit: String(limit),
      offset: String(offset),
    };
    if (type) {
      params.type = type;
    }
    return apiClient.get<SearchResponse>("/search", params);
  },

  /**
   * Execute an advanced search with filters.
   *
   * @param q - Search query string
   * @param params - Advanced filter parameters (type, date range, tags)
   */
  async searchAdvanced(
    q: string,
    params: AdvancedSearchParams = {},
  ): Promise<SearchResponse> {
    const queryParams: Record<string, string> = {
      q,
      limit: String(params.limit || 20),
      offset: String(params.offset || 0),
    };
    if (params.type) {
      queryParams.type = params.type;
    }
    if (params.date_from) {
      queryParams.date_from = params.date_from;
    }
    if (params.date_to) {
      queryParams.date_to = params.date_to;
    }
    if (params.tags && params.tags.length > 0) {
      queryParams.tags = params.tags.join(",");
    }
    return apiClient.get<SearchResponse>("/search/advanced", queryParams);
  },

  /**
   * Get autocomplete suggestions based on a partial query.
   *
   * @param q - Partial search query
   */
  async suggest(q: string): Promise<SuggestResponse> {
    return apiClient.get<SuggestResponse>("/search/suggest", { q });
  },
};
