/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Graph Service API Client
 */

import {
  NodeResponse,
  SubgraphResponse,
  NeighborResponse,
  GraphStatsResponse,
  RelatedEntitiesResponse,
  KnowledgeClustersResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

/**
 * Fetch a single graph node by ID
 */
export async function fetchNode(nodeId: string): Promise<NodeResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/graph/node/${nodeId}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch node:", error);
    return null;
  }
}

/**
 * Fetch a node with its direct neighbors
 */
export async function fetchNeighbors(
  nodeId: string,
  limit = 50,
): Promise<NeighborResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/graph/neighbors/${nodeId}?limit=${limit}`,
    );
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch neighbors:", error);
    return null;
  }
}

/**
 * Fetch a subgraph for visualization
 */
export async function fetchSubgraph(
  nodeId: string,
  depth = 2,
): Promise<SubgraphResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/graph/subgraph?node_id=${nodeId}&depth=${depth}`,
    );
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch subgraph:", error);
    return null;
  }
}

/**
 * Fetch graph statistics for the current user
 */
export async function fetchStats(): Promise<GraphStatsResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/graph/stats`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch stats:", error);
    return null;
  }
}

/**
 * Find all notes related to a given node
 */
export async function fetchRelatedNotes(
  nodeId: string,
  depth = 3,
  limit = 50,
): Promise<RelatedEntitiesResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/graph/find-related-notes/${nodeId}?depth=${depth}&limit=${limit}`,
    );
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch related notes:", error);
    return null;
  }
}

/**
 * Find all habits connected to a given node
 */
export async function fetchConnectedHabits(
  nodeId: string,
  depth = 3,
  limit = 50,
): Promise<RelatedEntitiesResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/graph/find-connected-habits/${nodeId}?depth=${depth}&limit=${limit}`,
    );
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch connected habits:", error);
    return null;
  }
}

/**
 * Find knowledge clusters (dense subgraphs) in the user's graph
 */
export async function fetchKnowledgeClusters(
  clusterThreshold = 3,
): Promise<KnowledgeClustersResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/graph/find-knowledge-clusters?cluster_threshold=${clusterThreshold}`,
    );
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch knowledge clusters:", error);
    return null;
  }
}
