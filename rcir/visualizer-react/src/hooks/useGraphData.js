import { useState, useEffect, useMemo, useCallback } from 'react';
import { computeHierarchicalFlowLayout, computeAdaptiveRadialLayout, computeForceLayout } from '../lib/graphLayout';

export function useGraphData(initialDatasetId = 'nextcloud') {
  const [datasetId, setDatasetId] = useState(initialDatasetId);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [highlightedNodes, setHighlightedNodes] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [layoutMode, setLayoutMode] = useState('3d'); // '3d' (default 3D WebGL) | 'flow' | 'force'

  // Fetch dataset JSON
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch(`/data/${datasetId}.json`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load /data/${datasetId}.json`);
        return res.json();
      })
      .then(json => {
        if (isMounted) {
          setData(json);
          setSelectedNode(null);
          setHoveredNode(null);
          setHighlightedNodes(null);
          setLoading(false);
        }
      })
      .catch(err => {
        if (isMounted) {
          console.error(err);
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [datasetId]);

  // Compute Layout when data or layoutMode changes
  const layout = useMemo(() => {
    if (!data) return { nodes: [], links: [] };

    // 3D mode uses ForceGraph3D WebGL canvas directly; do not run 2D d3 force simulation
    if (layoutMode === '3d') {
      return { nodes: [], links: [] };
    }

    if (layoutMode === 'flow') {
      return computeHierarchicalFlowLayout(data, 1300, 750);
    } else if (layoutMode === 'radial' && data.hierarchy) {
      return computeAdaptiveRadialLayout(data.hierarchy, 1300, 750);
    } else if (data.graph) {
      // Limit 2D force layout to top 150 nodes to avoid blocking the main thread
      const slicedNodes = (data.graph.nodes || []).slice(0, 150);
      const nodeSet = new Set(slicedNodes.map(n => n.path));
      const slicedEdges = (data.graph.edges || []).filter(e => nodeSet.has(e.source) && nodeSet.has(e.target)).slice(0, 300);
      return computeForceLayout(slicedNodes, slicedEdges, 1300, 750);
    }
    return { nodes: [], links: [] };
  }, [data, layoutMode]);

  // Precompute adjacency index for O(1) caller & callee retrieval across 143k edges
  const edgeIndex = useMemo(() => {
    if (!data?.graph?.edges) return { outgoing: new Map(), incoming: new Map() };
    const outgoing = new Map();
    const incoming = new Map();

    const edges = data.graph.edges;
    for (let i = 0; i < edges.length; i++) {
      const e = edges[i];
      if (!outgoing.has(e.source)) outgoing.set(e.source, []);
      outgoing.get(e.source).push(e);

      if (!incoming.has(e.target)) incoming.set(e.target, []);
      incoming.get(e.target).push(e);
    }
    return { outgoing, incoming };
  }, [data]);

  // Filtered nodes matching search query
  const matchingNodePaths = useMemo(() => {
    if (!searchQuery.trim() || !data) return null;
    const q = searchQuery.toLowerCase();
    const set = new Set();
    const nodes = data.graph?.nodes || [];
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      if ((n.path && n.path.toLowerCase().includes(q)) || (n.name && n.name.toLowerCase().includes(q))) {
        set.add(n.path);
        if (set.size >= 100) break; // Limit search result size for instant responsiveness
      }
    }
    return set;
  }, [searchQuery, data]);

  // Direct neighbors of selected node (incoming & outgoing) in O(1)
  const connectedNeighbors = useMemo(() => {
    if (!selectedNode || !edgeIndex) return null;
    const path = selectedNode.path || selectedNode.id;
    const neighbors = new Set([path]);
    const outEdges = edgeIndex.outgoing.get(path) || [];
    const inEdges = edgeIndex.incoming.get(path) || [];
    outEdges.forEach(e => neighbors.add(e.target));
    inEdges.forEach(e => neighbors.add(e.source));
    return neighbors;
  }, [selectedNode, edgeIndex]);

  const selectNodeByPath = useCallback((path) => {
    if (!path || !data?.graph?.nodes) {
      setSelectedNode(null);
      return;
    }
    const found = data.graph.nodes.find(n => n.path === path) ||
                  (data.hierarchy?.nodes || []).find(n => n.path === path);
    setSelectedNode(found || null);
  }, [data]);

  return {
    datasetId,
    setDatasetId,
    data,
    edgeIndex,
    loading,
    error,
    layout,
    layoutMode,
    setLayoutMode,
    selectedNode,
    setSelectedNode,
    hoveredNode,
    setHoveredNode,
    highlightedNodes,
    setHighlightedNodes,
    searchQuery,
    setSearchQuery,
    matchingNodePaths,
    connectedNeighbors,
    selectNodeByPath
  };
}
