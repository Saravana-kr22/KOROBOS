/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Interactive Force-Directed Graph Visualization with Zoom/Pan (Client-side)
 */

"use client";

import { useEffect, useState, useRef } from "react";
import { fetchSubgraph, fetchKnowledgeClusters } from "./graphApi";
import { SubgraphResponse, NodeResponse, EdgeResponse } from "./types";

interface GraphVisualizationProps {
  initialNodeId: string;
  depth?: number;
}

const TYPE_COLORS: Record<string, string> = {
  note: "#3b82f6", // blue
  habit: "#10b981", // green
  learning_topic: "#a855f7", // purple
  health_log: "#ef4444", // red
  database_record: "#6b7280", // gray
};

interface GraphNode {
  id: string;
  title: string;
  type: string;
  vx?: number;
  vy?: number;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
  cluster?: number; // Cluster ID for visualization
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  relation_type: string;
}

interface ViewTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

/**
 * Simple force-directed graph simulation with zoom/pan capabilities
 */
class ForceGraph {
  nodes: GraphNode[] = [];
  links: GraphLink[] = [];
  width: number;
  height: number;
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  running = true;
  selectedNodeId: string | null = null;

  // Zoom and pan
  scale = 1;
  offsetX = 0;
  offsetY = 0;
  minScale = 0.5;
  maxScale = 5;

  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.canvas = canvas;
    this.width = width;
    this.height = height;
    this.ctx = canvas.getContext("2d")!;
    canvas.width = width;
    canvas.height = height;
  }

  setData(nodes: NodeResponse[], edges: EdgeResponse[]) {
    this.nodes = nodes.map((n) => ({
      id: n.id,
      title: n.title,
      type: n.type,
      vx: 0,
      vy: 0,
      x: Math.random() * this.width,
      y: Math.random() * this.height,
    }));

    this.links = edges.map((e) => ({
      source: e.source_node_id,
      target: e.target_node_id,
      relation_type: e.relation_type,
    }));
  }

  setClusters(clusterMap: Record<string, number>) {
    for (const node of this.nodes) {
      node.cluster = clusterMap[node.id];
    }
  }

  simulate() {
    if (!this.running) return;

    // Apply forces
    this.applyRepulsiveForce();
    this.applyAttractiveForce();
    this.applyDampening();
    this.updatePositions();

    // Render with zoom/pan
    this.render();
    requestAnimationFrame(() => this.simulate());
  }

  private applyRepulsiveForce() {
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i];
        const n2 = this.nodes[j];
        const dx = (n2.x || 0) - (n1.x || 0);
        const dy = (n2.y || 0) - (n1.y || 0);
        const dist = Math.hypot(dx, dy) || 1;
        const force = -100 / (dist * dist);

        n1.vx! += (force * dx) / dist / 100;
        n1.vy! += (force * dy) / dist / 100;
        n2.vx! -= (force * dx) / dist / 100;
        n2.vy! -= (force * dy) / dist / 100;
      }
    }
  }

  private applyAttractiveForce() {
    for (const link of this.links) {
      const sourceId =
        typeof link.source === "string" ? link.source : link.source.id;
      const targetId =
        typeof link.target === "string" ? link.target : link.target.id;
      const n1 = this.nodes.find((n) => n.id === sourceId);
      const n2 = this.nodes.find((n) => n.id === targetId);

      if (!n1 || !n2) continue;

      const dx = (n2.x || 0) - (n1.x || 0);
      const dy = (n2.y || 0) - (n1.y || 0);
      const dist = Math.hypot(dx, dy) || 1;
      const force = Math.min(dist - 50, 100) / 50;

      n1.vx! += (force * dx) / dist / 10;
      n1.vy! += (force * dy) / dist / 10;
      n2.vx! -= (force * dx) / dist / 10;
      n2.vy! -= (force * dy) / dist / 10;
    }
  }

  private applyDampening() {
    for (const node of this.nodes) {
      node.vx! *= 0.95;
      node.vy! *= 0.95;
    }
  }

  private updatePositions() {
    for (const node of this.nodes) {
      if (node.fx !== undefined) {
        node.x = node.fx;
        node.y = node.fy;
      } else {
        node.x! += node.vx!;
        node.y! += node.vy!;
        // Boundary conditions
        node.x = Math.max(20, Math.min(this.width - 20, node.x));
        node.y = Math.max(20, Math.min(this.height - 20, node.y));
      }
    }
  }

  private render() {
    // Clear canvas
    this.ctx.fillStyle = "#f9fafb";
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Save context for transform
    this.ctx.save();

    // Apply zoom and pan transforms
    this.ctx.translate(this.offsetX, this.offsetY);
    this.ctx.scale(this.scale, this.scale);

    // Draw links
    this.ctx.strokeStyle = "#d1d5db";
    this.ctx.lineWidth = 1 / this.scale;
    for (const link of this.links) {
      const sourceId =
        typeof link.source === "string" ? link.source : link.source.id;
      const targetId =
        typeof link.target === "string" ? link.target : link.target.id;
      const n1 = this.nodes.find((n) => n.id === sourceId);
      const n2 = this.nodes.find((n) => n.id === targetId);
      if (!n1 || !n2) continue;

      this.ctx.beginPath();
      this.ctx.moveTo(n1.x || 0, n1.y || 0);
      this.ctx.lineTo(n2.x || 0, n2.y || 0);
      this.ctx.stroke();
    }

    // Draw nodes
    for (const node of this.nodes) {
      const color = TYPE_COLORS[node.type] || "#999";
      const isSelected = node.id === this.selectedNodeId;
      const size = isSelected ? 10 : 6;

      // Draw cluster background if part of cluster (light circle)
      if (node.cluster !== undefined) {
        const clusterAlpha = 0.1;
        this.ctx.fillStyle = this.getClusterColor(node.cluster, clusterAlpha);
        this.ctx.beginPath();
        this.ctx.arc(node.x || 0, node.y || 0, 30, 0, 2 * Math.PI);
        this.ctx.fill();
      }

      // Draw node circle
      this.ctx.fillStyle = color;
      this.ctx.beginPath();
      this.ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI);
      this.ctx.fill();

      // Draw border for selected node
      if (isSelected) {
        this.ctx.strokeStyle = "#000";
        this.ctx.lineWidth = 2 / this.scale;
        this.ctx.stroke();
      }

      // Draw label for selected node
      if (isSelected) {
        this.ctx.save();
        this.ctx.scale(1 / this.scale, 1 / this.scale);
        this.ctx.fillStyle = "#000";
        this.ctx.font = `${12 / this.scale}px sans-serif`;
        this.ctx.textAlign = "center";
        const screenX = (node.x || 0) * this.scale + this.offsetX;
        const screenY = (node.y || 0) * this.scale + this.offsetY;
        this.ctx.fillText(node.title.substring(0, 15), screenX, screenY + 20);
        this.ctx.restore();
      }
    }

    this.ctx.restore();
  }

  private getClusterColor(clusterId: number, alpha: number): string {
    const colors = [
      `rgba(59, 130, 246, ${alpha})`, // blue
      `rgba(16, 185, 129, ${alpha})`, // green
      `rgba(168, 85, 247, ${alpha})`, // purple
      `rgba(239, 68, 68, ${alpha})`, // red
      `rgba(107, 114, 128, ${alpha})`, // gray
    ];
    return colors[clusterId % colors.length];
  }

  getNodeAtPoint(x: number, y: number): GraphNode | null {
    // Convert screen coordinates to graph coordinates
    const graphX = (x - this.offsetX) / this.scale;
    const graphY = (y - this.offsetY) / this.scale;

    for (const node of this.nodes) {
      const dist = Math.hypot((node.x || 0) - graphX, (node.y || 0) - graphY);
      if (dist < 10 / this.scale) return node;
    }
    return null;
  }

  dragNode(nodeId: string, x: number, y: number) {
    const graphX = (x - this.offsetX) / this.scale;
    const graphY = (y - this.offsetY) / this.scale;

    const node = this.nodes.find((n) => n.id === nodeId);
    if (node) {
      node.fx = graphX;
      node.fy = graphY;
    }
  }

  releaseNode(nodeId: string) {
    const node = this.nodes.find((n) => n.id === nodeId);
    if (node) {
      node.fx = undefined;
      node.fy = undefined;
    }
  }

  zoom(factor: number) {
    const newScale = Math.max(
      this.minScale,
      Math.min(this.maxScale, this.scale * factor),
    );
    this.scale = newScale;
  }

  pan(dx: number, dy: number) {
    this.offsetX += dx;
    this.offsetY += dy;
  }

  resetView() {
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;
  }

  stop() {
    this.running = false;
  }
}

export default function GraphVisualization({
  initialNodeId,
  depth = 2,
}: GraphVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const graphRef = useRef<ForceGraph | null>(null);
  const [subgraph, setSubgraph] = useState<SubgraphResponse | null>(null);
  const [selectedNode, setSelectedNode] = useState<NodeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showClusters, setShowClusters] = useState(false);

  // Load subgraph data
  useEffect(() => {
    const loadSubgraph = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSubgraph(initialNodeId, depth);
        if (data) {
          setSubgraph(data);
          if (data.nodes.length > 0) {
            setSelectedNode(data.nodes[0]);
          }
        } else {
          setError("Failed to load graph data");
        }
      } catch (err) {
        setError("Error loading graph: " + String(err));
      } finally {
        setLoading(false);
      }
    };

    loadSubgraph();
  }, [initialNodeId, depth]);

  // Initialize force graph
  useEffect(() => {
    if (!subgraph || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const graph = new ForceGraph(
      canvas,
      canvas.offsetWidth,
      canvas.offsetHeight,
    );
    graph.setData(subgraph.nodes, subgraph.edges);

    if (selectedNode) {
      graph.selectedNodeId = selectedNode.id;
    }

    graphRef.current = graph;
    graph.simulate();

    return () => {
      graph.stop();
    };
  }, [subgraph]);

  // Load and set clusters if enabled
  useEffect(() => {
    if (!showClusters || !graphRef.current) return;

    const loadClusters = async () => {
      try {
        const response = await fetchKnowledgeClusters();
        if (response && response.clusters) {
          const clusterMap: Record<string, number> = {};
          response.clusters.forEach((cluster, idx) => {
            cluster.node_ids.forEach((nodeId: string) => {
              clusterMap[nodeId] = idx;
            });
          });
          graphRef.current?.setClusters(clusterMap);
        }
      } catch (err) {
        console.error("Failed to load clusters:", err);
      }
    };

    loadClusters();
  }, [showClusters]);

  // Update selected node in graph
  useEffect(() => {
    if (graphRef.current && selectedNode) {
      graphRef.current.selectedNodeId = selectedNode.id;
    }
  }, [selectedNode]);

  // Handle zoom via mouse wheel
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    if (!graphRef.current) return;

    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    graphRef.current.zoom(factor);
    setZoom(graphRef.current.scale);
  };

  // Handle canvas click
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graphRef.current || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const node = graphRef.current.getNodeAtPoint(x, y);
    if (node && subgraph) {
      const fullNode = subgraph.nodes.find((n) => n.id === node.id);
      if (fullNode) {
        setSelectedNode(fullNode);
      }
    }
  };

  // Handle mouse down for dragging
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graphRef.current || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const node = graphRef.current.getNodeAtPoint(x, y);
    if (node) {
      setDraggedNodeId(node.id);
    }
  };

  // Handle mouse move for dragging
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggedNodeId || !graphRef.current || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    graphRef.current.dragNode(draggedNodeId, x, y);
  };

  // Handle mouse up for dragging
  const handleMouseUp = () => {
    if (draggedNodeId && graphRef.current) {
      graphRef.current.releaseNode(draggedNodeId);
      setDraggedNodeId(null);
    }
  };

  // Reset view
  const handleResetView = () => {
    if (graphRef.current) {
      graphRef.current.resetView();
      setZoom(1);
    }
  };

  if (loading) {
    return <div className="p-4 text-center">Loading graph...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (!subgraph) {
    return <div className="p-4 text-gray-500">No graph data available</div>;
  }

  return (
    <div className="flex h-screen gap-4">
      {/* Canvas Area */}
      <div className="flex-1 border border-gray-300 rounded bg-gray-50 relative overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-grab active:cursor-grabbing"
          onClick={handleCanvasClick}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          title="Scroll to zoom • Click to select • Drag to move nodes"
        />

        {/* Top-left controls */}
        <div className="absolute top-4 left-4 bg-white p-3 rounded shadow text-sm space-y-1">
          <p>
            <strong>Nodes:</strong> {subgraph.nodes.length}
          </p>
          <p>
            <strong>Edges:</strong> {subgraph.edges.length}
          </p>
          <p className="text-xs text-gray-600 mt-2">
            Scroll to zoom • Click to select
          </p>
          <p className="text-xs text-gray-600">Drag nodes to move</p>
        </div>

        {/* Zoom controls */}
        <div className="absolute bottom-4 left-4 bg-white p-2 rounded shadow space-y-1">
          <button
            onClick={() => graphRef.current?.zoom(1.2)}
            className="w-full px-2 py-1 text-sm bg-blue-50 hover:bg-blue-100 rounded"
            title="Zoom in"
          >
            +
          </button>
          <div className="text-center text-xs text-gray-600 px-2 py-1">
            {(zoom * 100).toFixed(0)}%
          </div>
          <button
            onClick={() => graphRef.current?.zoom(0.8)}
            className="w-full px-2 py-1 text-sm bg-blue-50 hover:bg-blue-100 rounded"
            title="Zoom out"
          >
            −
          </button>
          <button
            onClick={handleResetView}
            className="w-full px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded mt-2"
            title="Reset view"
          >
            Reset
          </button>
        </div>

        {/* Cluster toggle */}
        <div className="absolute top-4 right-4 bg-white p-3 rounded shadow text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showClusters}
              onChange={(e) => setShowClusters(e.target.checked)}
              className="w-4 h-4"
            />
            <span>Show Clusters</span>
          </label>
        </div>
      </div>

      {/* Sidebar: Node Details */}
      <div className="w-80 border-l border-gray-300 p-4 overflow-y-auto bg-white">
        <h2 className="text-lg font-bold mb-4">Graph Details</h2>

        {selectedNode ? (
          <div className="space-y-4">
            {/* Node Info */}
            <div className="bg-gray-100 p-3 rounded">
              <div
                className="w-3 h-3 rounded-full mb-2"
                style={{
                  backgroundColor: TYPE_COLORS[selectedNode.type] || "#999",
                }}
              />
              <h3 className="font-semibold text-lg">{selectedNode.title}</h3>
              <p className="text-sm text-gray-600 mt-1">
                <span className="font-mono text-xs bg-white px-2 py-1 rounded">
                  {selectedNode.type}
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Created:{" "}
                {new Date(selectedNode.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* Related Nodes */}
            {subgraph && (
              <div>
                <h4 className="font-semibold text-sm mb-2">Connected Nodes</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {subgraph.edges
                    .filter(
                      (e) =>
                        e.source_node_id === selectedNode.id ||
                        e.target_node_id === selectedNode.id,
                    )
                    .map((edge) => {
                      const relatedNodeId =
                        edge.source_node_id === selectedNode.id
                          ? edge.target_node_id
                          : edge.source_node_id;
                      const relatedNode = subgraph.nodes.find(
                        (n) => n.id === relatedNodeId,
                      );
                      return (
                        <button
                          key={edge.id}
                          onClick={() =>
                            relatedNode && setSelectedNode(relatedNode)
                          }
                          className="w-full text-left p-2 bg-gray-100 hover:bg-blue-50 rounded text-sm transition"
                        >
                          <p className="font-medium text-sm">
                            {relatedNode?.title}
                          </p>
                          <p className="text-xs text-gray-600 mt-1">
                            {edge.relation_type}
                          </p>
                        </button>
                      );
                    })
                    .slice(0, 10)}
                  {subgraph.edges.filter(
                    (e) =>
                      e.source_node_id === selectedNode.id ||
                      e.target_node_id === selectedNode.id,
                  ).length === 0 && (
                    <p className="text-xs text-gray-500">No connected nodes</p>
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            {selectedNode.metadata &&
              Object.keys(selectedNode.metadata).length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2">Metadata</h4>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-40 text-gray-700">
                    {JSON.stringify(selectedNode.metadata, null, 2)}
                  </pre>
                </div>
              )}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Select a node to view details</p>
        )}
      </div>
    </div>
  );
}
