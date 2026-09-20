import { useState, useEffect, useMemo, useCallback } from 'react';
import { computeHierarchicalFlowLayout, computeAdaptiveRadialLayout, computeForceLayout } from '../lib/graphLayout';

export function useGraphData(initialDatasetId = 'otel_recommendation') {
  const [datasetId, setDatasetId] = useState(initialDatasetId);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [highlightedNodes, setHighlightedNodes] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [layoutMode, setLayoutMode] = useState('flow'); // 'flow' (default DAG) | 'radial' | 'force'

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

    if (layoutMode === 'flow') {
      return computeHierarchicalFlowLayout(data, 1300, 750);
    } else if (layoutMode === 'radial' && data.hierarchy) {
      return computeAdaptiveRadialLayout(data.hierarchy, 1300, 750);
    } else if (data.graph) {
      return computeForceLayout(data.graph.nodes, data.graph.edges, 1300, 750);
    }
    return { nodes: [], links: [] };
  }, [data, layoutMode]);

  // Filtered nodes matching search query
  const matchingNodePaths = useMemo(() => {
    if (!searchQuery.trim() || !data) return null;
    const q = searchQuery.toLowerCase();
    const set = new Set();
    (data.graph?.nodes || []).forEach(n => {
      if ((n.path && n.path.toLowerCase().includes(q)) || (n.kind && n.kind.toLowerCase().includes(q))) {
        set.add(n.path);
      }
    });
    return set;
  }, [searchQuery, data]);

  // Direct neighbors of selected node (incoming & outgoing)
  const connectedNeighbors = useMemo(() => {
    if (!selectedNode || !data?.graph?.edges) return null;
    const neighbors = new Set([selectedNode.path]);
    data.graph.edges.forEach(e => {
      if (e.source === selectedNode.path) neighbors.add(e.target);
      if (e.target === selectedNode.path) neighbors.add(e.source);
    });
    return neighbors;
  }, [selectedNode, data]);

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
