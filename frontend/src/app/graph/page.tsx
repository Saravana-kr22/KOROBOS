/**
 * KOROBOS — Second Brain Operating System
 *
 * Copyright (c) 2026 Saravana Perumal K
 *
 * Licensed under the GNU Affero General Public License v3.
 *
 * Knowledge Graph Visualization Page
 */

import { Suspense } from "react";
import GraphVisualization from "./GraphVisualization";

// Placeholder for a real initial node ID from the user's profile or URL params
const DEFAULT_NODE_ID = "550e8400-e29b-41d4-a716-446655440000";

export const metadata = {
  title: "Knowledge Graph",
  description:
    "Visualize your connected knowledge across notes, habits, learning, and more",
};

export default function GraphPage() {
  return (
    <div className="w-full h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-3xl font-bold">Knowledge Graph</h1>
        <p className="text-gray-600 mt-1">
          Explore relationships between your notes, habits, learning topics, and
          more
        </p>
      </header>

      <main className="flex-1 overflow-hidden">
        <Suspense
          fallback={<div className="p-4">Loading graph visualization...</div>}
        >
          <GraphVisualization initialNodeId={DEFAULT_NODE_ID} depth={2} />
        </Suspense>
      </main>
    </div>
  );
}
