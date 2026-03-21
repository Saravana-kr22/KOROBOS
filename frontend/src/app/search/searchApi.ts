/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search API client for the web frontend (Next.js).
Provides typed fetch wrappers for search endpoints.
*/

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
 * Search API client — provides typed fetch wrappers for search endpoints.
 * All methods take a token as the first argument for authentication.
 */
export const searchApi = {
  /**
   * Execute a basic search across all domains.
   *
   * @param token - JWT auth token
   * @param q - Search query string
   * @param type - Optional type filter (note, habit, learning, record, meal, workout)
   * @param limit - Results per page (default 20, max 50)
   * @param offset - Pagination offset (default 0)
   */
  async search(
    token: string,
    q: string,
    type?: string,
    limit: number = 20,
    offset: number = 0,
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q,
      limit: String(limit),
      offset: String(offset),
    });
    if (type) {
      params.append("type", type);
    }

    const res = await fetch(`/api/v1/search?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      throw new Error(`Search failed: ${res.status} ${res.statusText}`);
    }

    return res.json();
  },

  /**
   * Execute an advanced search with filters.
   *
   * @param token - JWT auth token
   * @param q - Search query string
   * @param params - Advanced filter parameters (type, date range, tags)
   */
  async searchAdvanced(
    token: string,
    q: string,
    params: AdvancedSearchParams = {},
  ): Promise<SearchResponse> {
    const queryParams = new URLSearchParams({
      q,
      limit: String(params.limit || 20),
      offset: String(params.offset || 0),
    });

    if (params.type) {
      queryParams.append("type", params.type);
    }
    if (params.date_from) {
      queryParams.append("date_from", params.date_from);
    }
    if (params.date_to) {
      queryParams.append("date_to", params.date_to);
    }
    if (params.tags && params.tags.length > 0) {
      queryParams.append("tags", params.tags.join(","));
    }

    const res = await fetch(
      `/api/v1/search/advanced?${queryParams.toString()}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!res.ok) {
      throw new Error(
        `Advanced search failed: ${res.status} ${res.statusText}`,
      );
    }

    return res.json();
  },

  /**
   * Get autocomplete suggestions based on a partial query.
   *
   * @param token - JWT auth token
   * @param q - Partial search query
   */
  async suggest(token: string, q: string): Promise<SuggestResponse> {
    const res = await fetch(
      `/api/v1/search/suggest?q=${encodeURIComponent(q)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!res.ok) {
      throw new Error(`Suggest failed: ${res.status} ${res.statusText}`);
    }

    return res.json();
  },
};
