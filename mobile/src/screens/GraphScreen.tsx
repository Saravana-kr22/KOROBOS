/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Mobile Graph Visualization Screen (React Native) with Visual Graph
 */

import React, { useEffect, useState } from "react";
import {
  View,
  ScrollView,
  Text,
  Pressable,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
} from "react-native";
import { graphService } from "../services/graphService";
import { SubgraphResponse, NodeResponse, EdgeResponse } from "../types/graph";

interface GraphScreenProps {
  route?: any;
  navigation?: any;
}

const TYPE_COLORS: Record<string, string> = {
  note: "#3b82f6",
  habit: "#10b981",
  learning_topic: "#a855f7",
  health_log: "#ef4444",
  database_record: "#6b7280",
};

/**
 * Simple node-link diagram layout calculator
 */
function layoutNodes(
  nodes: NodeResponse[],
  edges: EdgeResponse[],
  width: number,
  height: number,
) {
  const positions: Record<string, { x: number; y: number }> = {};
  const nodeCount = nodes.length;

  if (nodeCount === 0) return positions;
  if (nodeCount === 1) {
    positions[nodes[0].id] = { x: width / 2, y: height / 2 };
    return positions;
  }

  // Simple radial layout
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;

  nodes.forEach((node, index) => {
    const angle = (index / nodeCount) * 2 * Math.PI;
    positions[node.id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  return positions;
}

export const GraphScreen: React.FC<GraphScreenProps> = ({
  route,
  navigation,
}) => {
  const initialNodeId =
    route?.params?.nodeId || "550e8400-e29b-41d4-a716-446655440000";
  const screenWidth = Dimensions.get("window").width;
  const graphHeight = 250;

  const [currentNode, setCurrentNode] = useState<NodeResponse | null>(null);
  const [subgraph, setSubgraph] = useState<SubgraphResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [neighborOffset, setNeighborOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [focusMode, setFocusMode] = useState(true); // Simplified view by default
  const [holdNodeId, setHoldNodeId] = useState<string | null>(null);
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(
    null,
  );
  const NEIGHBORS_PER_PAGE = 10;
  const LONG_PRESS_DURATION = 500; // ms

  // Load initial node and subgraph
  useEffect(() => {
    loadNode(initialNodeId);
  }, [initialNodeId]);

  const loadNode = async (nodeId: string) => {
    setLoading(true);
    setError(null);
    setNeighborOffset(0); // Reset pagination when changing nodes
    try {
      const node = await graphService.fetchNode(nodeId);
      const graph = await graphService.fetchSubgraph(nodeId, 2);

      if (node && graph) {
        setCurrentNode(node);
        setSubgraph(graph);
        setSelectedNodeId(nodeId);
      } else {
        setError("Failed to load node");
      }
    } catch (err) {
      setError("Error: " + String(err));
    } finally {
      setLoading(false);
    }
  };

  const loadMoreNeighbors = async () => {
    if (!currentNode) return;

    setLoadingMore(true);
    try {
      const newOffset = neighborOffset + NEIGHBORS_PER_PAGE;
      const neighbors = await graphService.fetchNeighbors(
        currentNode.id,
        NEIGHBORS_PER_PAGE,
        newOffset,
      );

      if (neighbors && subgraph) {
        // Merge new neighbors with existing ones, avoiding duplicates
        const newNodeIds = new Set(subgraph.nodes.map((n) => n.id));
        const uniqueNewNeighbors = neighbors.neighbors.filter(
          (n) => !newNodeIds.has(n.id),
        );

        setSubgraph({
          nodes: [...subgraph.nodes, ...uniqueNewNeighbors],
          edges: [...subgraph.edges, ...neighbors.edges],
        });

        setNeighborOffset(newOffset);
      }
    } catch (err) {
      setError("Error loading more: " + String(err));
    } finally {
      setLoadingMore(false);
    }
  };

  // Handle node tap: select vs navigate based on duration
  const handleNodePressIn = (nodeId: string) => {
    setHoldNodeId(nodeId);

    const timer = setTimeout(() => {
      // Long press (500ms+): navigate to node
      if (currentNode?.id !== nodeId) {
        loadNode(nodeId);
      }
      setHoldNodeId(null);
    }, LONG_PRESS_DURATION);

    setLongPressTimer(timer);
  };

  const handleNodePressOut = (nodeId: string) => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
    }

    // Short tap: select node (show details)
    if (holdNodeId === nodeId) {
      setSelectedNodeId(nodeId);
      setHoldNodeId(null);
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  if (!currentNode || !subgraph) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>No node data available</Text>
      </View>
    );
  }

  const positions = layoutNodes(
    subgraph.nodes,
    subgraph.edges,
    screenWidth - 32,
    graphHeight,
  );

  // Filter neighbors for current node
  const connectedEdges = subgraph.edges.filter(
    (e) =>
      e.source_node_id === currentNode.id ||
      e.target_node_id === currentNode.id,
  );

  const neighbors = connectedEdges
    .map((edge) => {
      const neighborId =
        edge.source_node_id === currentNode.id
          ? edge.target_node_id
          : edge.source_node_id;
      return subgraph.nodes.find((n) => n.id === neighborId);
    })
    .filter((n): n is NodeResponse => n !== undefined);

  // Focus view: only show current node and direct neighbors
  const displayNodes = focusMode ? [currentNode, ...neighbors] : subgraph.nodes;

  const displayEdges = focusMode ? connectedEdges : subgraph.edges;

  return (
    <ScrollView style={styles.scrollContainer}>
      {/* Graph Visualization */}
      <View style={styles.graphContainer}>
        <Text style={styles.graphTitle}>Knowledge Graph</Text>
        <View
          style={[
            styles.graphCanvas,
            { width: screenWidth - 32, height: graphHeight },
          ]}
        >
          {/* Render edges (lines) */}
          {displayEdges.map((edge) => {
            const sourcePos = positions[edge.source_node_id];
            const targetPos = positions[edge.target_node_id];
            if (!sourcePos || !targetPos) return null;

            const dx = targetPos.x - sourcePos.x;
            const dy = targetPos.y - sourcePos.y;
            const distance = Math.hypot(dx, dy);
            const angle = Math.atan2(dy, dx);

            return (
              <View
                key={edge.id}
                style={[
                  styles.graphEdge,
                  {
                    left: sourcePos.x,
                    top: sourcePos.y,
                    width: distance,
                    transform: [{ rotate: `${angle}rad` }],
                  },
                ]}
              />
            );
          })}

          {/* Render nodes (circles) */}
          {displayNodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;

            const isSelected = node.id === selectedNodeId;
            const isCurrent = node.id === currentNode.id;
            const isHeld = node.id === holdNodeId;

            return (
              <Pressable
                key={node.id}
                style={[
                  styles.graphNode,
                  {
                    left: pos.x - 16,
                    top: pos.y - 16,
                    backgroundColor: TYPE_COLORS[node.type] || "#999",
                    borderWidth: isCurrent
                      ? 3
                      : isSelected
                      ? 2
                      : isHeld
                      ? 1.5
                      : 0,
                    borderColor: isCurrent
                      ? "#000"
                      : isSelected
                      ? "#000"
                      : isHeld
                      ? "#3b82f6"
                      : "transparent",
                    opacity: isHeld ? 0.8 : 1,
                  },
                ]}
                onPressIn={() => handleNodePressIn(node.id)}
                onPressOut={() => handleNodePressOut(node.id)}
              />
            );
          })}
        </View>
        <Text style={styles.graphLegend}>
          {displayNodes.length} nodes • {displayEdges.length} connections{" "}
          {focusMode && "(Focus Mode)"}
        </Text>
      </View>

      {/* Current Node Card with Controls */}
      <View style={styles.nodeCard}>
        <View
          style={[
            styles.typeIndicator,
            { backgroundColor: TYPE_COLORS[currentNode.type] || "#999" },
          ]}
        />
        <View style={styles.nodeContent}>
          <Text style={styles.nodeTitle}>{currentNode.title}</Text>
          <Text style={styles.nodeType}>{currentNode.type}</Text>
          <Text style={styles.nodeDate}>
            {new Date(currentNode.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>

      {/* View Controls */}
      <View style={styles.controlsSection}>
        <Pressable
          style={[
            styles.controlButton,
            focusMode && styles.controlButtonActive,
          ]}
          onPress={() => setFocusMode(!focusMode)}
        >
          <Text
            style={[
              styles.controlButtonText,
              focusMode && styles.controlButtonTextActive,
            ]}
          >
            {focusMode ? "🎯 Focus View" : "📊 Full Graph"}
          </Text>
        </Pressable>
      </View>

      {/* Neighbors Section */}
      <View style={styles.neighborsSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            Connected Nodes ({neighbors.length})
          </Text>
          {neighbors.length > NEIGHBORS_PER_PAGE && (
            <Text style={styles.pageIndicator}>
              Page {Math.floor(neighborOffset / NEIGHBORS_PER_PAGE) + 1}
            </Text>
          )}
        </View>

        <View>
          {neighbors.length > 0 ? (
            <>
              {neighbors.slice(0, NEIGHBORS_PER_PAGE).map((neighbor) => {
                const relatedEdge = connectedEdges.find(
                  (e) =>
                    (e.source_node_id === currentNode.id &&
                      e.target_node_id === neighbor.id) ||
                    (e.target_node_id === currentNode.id &&
                      e.source_node_id === neighbor.id),
                );

                return (
                  <Pressable
                    key={neighbor.id}
                    style={styles.neighborItem}
                    onPress={() => loadNode(neighbor.id)}
                  >
                    <View
                      style={[
                        styles.neighborColor,
                        {
                          backgroundColor: TYPE_COLORS[neighbor.type] || "#999",
                        },
                      ]}
                    />
                    <View style={styles.neighborInfo}>
                      <Text style={styles.neighborTitle}>{neighbor.title}</Text>
                      {relatedEdge && (
                        <Text style={styles.relationshipType}>
                          {relatedEdge.relation_type}
                        </Text>
                      )}
                    </View>
                  </Pressable>
                );
              })}

              {neighbors.length > NEIGHBORS_PER_PAGE && (
                <Pressable
                  style={[styles.neighborItem, styles.loadMoreButton]}
                  onPress={loadMoreNeighbors}
                  disabled={loadingMore}
                >
                  <Text style={styles.loadMoreText}>
                    {loadingMore
                      ? "Loading..."
                      : `Load More (${
                          neighbors.length - NEIGHBORS_PER_PAGE
                        } more)`}
                  </Text>
                </Pressable>
              )}
            </>
          ) : (
            <Text style={styles.noNeighbors}>No connected nodes</Text>
          )}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scrollContainer: {
    flex: 1,
    backgroundColor: "#f9fafb",
  },
  container: {
    flex: 1,
    backgroundColor: "#f9fafb",
    justifyContent: "center",
    alignItems: "center",
  },
  graphContainer: {
    backgroundColor: "white",
    margin: 16,
    borderRadius: 8,
    padding: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 3,
  },
  graphTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111",
    marginBottom: 8,
  },
  graphCanvas: {
    backgroundColor: "#f3f4f6",
    borderRadius: 6,
    position: "relative",
    overflow: "hidden",
  },
  graphEdge: {
    position: "absolute",
    height: 1,
    backgroundColor: "#d1d5db",
    transformOrigin: "0 0",
  },
  graphNode: {
    position: "absolute",
    width: 32,
    height: 32,
    borderRadius: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  graphLegend: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 8,
    textAlign: "center",
  },
  nodeCard: {
    backgroundColor: "white",
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 8,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 3,
  },
  typeIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  nodeContent: {
    flex: 1,
  },
  nodeTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111",
    marginBottom: 4,
  },
  nodeType: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 2,
  },
  nodeDate: {
    fontSize: 11,
    color: "#9ca3af",
  },
  neighborsSection: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111",
    marginBottom: 12,
  },
  neighborItem: {
    backgroundColor: "white",
    borderRadius: 6,
    padding: 12,
    marginBottom: 8,
    flexDirection: "row",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1.41,
    elevation: 2,
  },
  neighborColor: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  neighborInfo: {
    flex: 1,
  },
  neighborTitle: {
    fontSize: 13,
    fontWeight: "500",
    color: "#111",
    marginBottom: 2,
  },
  relationshipType: {
    fontSize: 11,
    color: "#6b7280",
    fontStyle: "italic",
  },
  noNeighbors: {
    color: "#9ca3af",
    textAlign: "center",
    marginTop: 12,
    fontSize: 13,
  },
  error: {
    color: "#ef4444",
    fontSize: 14,
    textAlign: "center",
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  pageIndicator: {
    fontSize: 11,
    color: "#9ca3af",
    backgroundColor: "#f3f4f6",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  loadMoreButton: {
    backgroundColor: "#f0f9ff",
    borderColor: "#3b82f6",
    borderWidth: 1,
    marginTop: 8,
  },
  loadMoreText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#3b82f6",
    textAlign: "center",
    width: "100%",
  },
  controlsSection: {
    marginHorizontal: 16,
    marginBottom: 12,
    flexDirection: "row",
    gap: 8,
  },
  controlButton: {
    flex: 1,
    backgroundColor: "#f3f4f6",
    borderRadius: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  controlButtonActive: {
    backgroundColor: "#dbeafe",
    borderColor: "#3b82f6",
  },
  controlButtonText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#6b7280",
  },
  controlButtonTextActive: {
    color: "#3b82f6",
  },
});

export default GraphScreen;
