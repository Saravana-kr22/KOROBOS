/*
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * AI Service API client for mobile.
 */

import { apiClient } from "../services/apiClient";

export interface Insight {
  id: string;
  user_id: string;
  insight_type: "behavioral" | "performance" | "health" | "knowledge";
  text: string;
  confidence: number;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface Recommendation {
  id: string;
  user_id: string;
  category: "habit" | "learning" | "health" | "productivity";
  text: string;
  priority: "high" | "medium" | "low";
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface Summary {
  user_id: string;
  summary: string;
  generated_at: string;
  insights: Insight[];
  recommendations: Recommendation[];
}

/**
 * Get user's insights with optional filtering
 */
export const getInsights = async (
  insightType?: string,
  limit: number = 10,
): Promise<{ insights: Insight[]; total: number }> => {
  const params = new URLSearchParams();
  if (insightType) params.append("insight_type", insightType);
  params.append("limit", limit.toString());

  const response = await apiClient.get(`/ai/insights?${params.toString()}`);
  return response.data;
};

/**
 * Get user's recommendations with optional filtering
 */
export const getRecommendations = async (
  category?: string,
  limit: number = 10,
): Promise<{ recommendations: Recommendation[]; total: number }> => {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  params.append("limit", limit.toString());

  const response = await apiClient.get(
    `/ai/recommendations?${params.toString()}`,
  );
  return response.data;
};

/**
 * Get aggregated summary of insights and recommendations
 */
export const getSummary = async (): Promise<Summary> => {
  const response = await apiClient.get("/ai/summary");
  return response.data;
};

/**
 * Create a custom AI prompt and get response
 */
export const createPrompt = async (
  prompt: string,
  interactionType:
    | "recommendation"
    | "summary"
    | "assistant"
    | "gap_analysis"
    | "study_optimization" = "assistant",
  metadataJson?: Record<string, any>,
) => {
  const response = await apiClient.post("/ai/prompt", {
    prompt,
    interaction_type: interactionType,
    metadata_json: metadataJson,
  });
  return response.data;
};

/**
 * List user's AI interactions (chat history)
 */
export const listInteractions = async (
  offset: number = 0,
  limit: number = 50,
) => {
  const response = await apiClient.get(
    `/ai/interactions?offset=${offset}&limit=${limit}`,
  );
  return response.data;
};
