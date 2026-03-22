/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * TypeScript types for Graph API
 */

export interface NodeResponse {
  id: string;
  user_id: string;
  type: "note" | "habit" | "learning_topic" | "health_log" | "database_record";
  title: string;
  source_id: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface EdgeResponse {
  id: string;
  user_id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: string;
  created_at: string;
}

export interface SubgraphResponse {
  nodes: NodeResponse[];
  edges: EdgeResponse[];
}

export interface NeighborResponse {
  node: NodeResponse;
  edges: EdgeResponse[];
  neighbors: NodeResponse[];
}

export interface GraphStatsResponse {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  relation_types: Record<string, number>;
}

// For visualization with react-force-graph-2d
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  color: string;
  size: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface RelatedEntitiesResponse {
  entity_type:
    | "note"
    | "habit"
    | "learning_topic"
    | "health_log"
    | "database_record";
  count: number;
  nodes: NodeResponse[];
}

export interface KnowledgeClusterResponse {
  cluster_id: number;
  size: number;
  node_ids: string[];
  nodes: NodeResponse[];
}

export interface KnowledgeClustersResponse {
  total_clusters: number;
  clusters: KnowledgeClusterResponse[];
}
