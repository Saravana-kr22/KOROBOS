/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Mobile API Client for Graph Service
 */

import {
  NodeResponse,
  NeighborResponse,
  SubgraphResponse,
} from "../types/graph";

const API_BASE = "http://localhost:8080/api/v1"; // Configure for your environment

class GraphService {
  /**
   * Fetch a single graph node by ID
   */
  async fetchNode(nodeId: string): Promise<NodeResponse | null> {
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
   * Fetch a node with its direct neighbors (with pagination support)
   * @param nodeId - The node ID to fetch neighbors for
   * @param limit - Number of neighbors per page (default: 10 for mobile)
   * @param offset - Pagination offset (default: 0)
   */
  async fetchNeighbors(
    nodeId: string,
    limit = 10,
    offset = 0,
  ): Promise<NeighborResponse | null> {
    try {
      const url = new URL(`${API_BASE}/graph/neighbors/${nodeId}`);
      url.searchParams.append("limit", String(limit));
      url.searchParams.append("offset", String(offset));

      const response = await fetch(url.toString());
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
  async fetchSubgraph(
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
}

// Export singleton instance
export const graphService = new GraphService();
