import React, { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph3D from '3d-force-graph';
import { 
  Compass, 
  Maximize2, 
  RotateCcw, 
  Filter, 
  Search, 
  Layers, 
  Sparkles,
  Zap,
  Eye,
  Sliders
} from 'lucide-react';
import { getNodeColor, LEVEL_COLORS } from '../lib/colors';

export function Graph3DCanvas({
  data,
  selectedNode,
  onSelectNode,
  searchQuery,
  onResetCamera
}) {
  const mountRef = useRef(null);
  const graphInstanceRef = useRef(null);

  const [moduleFilter, setModuleFilter] = useState('all');
  const [kindFilter, setKindFilter] = useState('all');
  const [maxNodes, setMaxNodes] = useState(600);

  // Extract raw nodes and edges from dataset
  const rawNodes = data?.graph?.nodes || [];
  const rawEdges = data?.graph?.edges || [];

  // Filter nodes and edges based on user selection
  const filteredGraphData = useMemo(() => {
    if (!rawNodes || rawNodes.length === 0) {
      return { nodes: [], links: [] };
    }

    const query = (searchQuery || '').trim().toLowerCase();

    // Step 1: Filter nodes
    let nodes = rawNodes.filter(n => {
      const p = (n.path || '').toLowerCase();
      const kind = (n.kind || n.level || '').toLowerCase();

      // Module filter
      if (moduleFilter === 'files' && !p.includes('apps/files')) return false;
      if (moduleFilter === 'dav' && !p.includes('apps/dav')) return false;
      if (moduleFilter === 'ocp' && !p.includes('lib/public')) return false;
      if (moduleFilter === 'private' && !p.includes('lib/private')) return false;

      // Kind filter
      if (kindFilter === 'classes' && !(kind === 'class' || kind === 'interface' || kind === 'trait')) return false;
      if (kindFilter === 'methods' && !(kind === 'method' || kind === 'function')) return false;
      if (kindFilter === 'files' && kind !== 'file') return false;

      return true;
    });

    // If search query is present, prioritize search matches
    if (query) {
      nodes = nodes.filter(n => (n.path || '').toLowerCase().includes(query) || (n.name || '').toLowerCase().includes(query));
    }

    // Limit to maxNodes for 60 FPS responsiveness
    const slicedNodes = nodes.slice(0, maxNodes);
    const validNodePaths = new Set(slicedNodes.map(n => n.path));

    // Step 2: Filter edges connecting valid nodes
    const links = [];
    const seen = new Set();

    for (const e of rawEdges) {
      if (validNodePaths.has(e.source) && validNodePaths.has(e.target) && e.source !== e.target) {
        const key = `${e.source}->${e.target}`;
        if (!seen.has(key)) {
          seen.add(key);
          links.push({
            source: e.source,
            target: e.target,
            edge_type: e.type || e.edge_type || 'calls'
          });
        }
      }
    }

    return {
      nodes: slicedNodes.map(n => ({
        ...n,
        id: n.path,
        name: n.name || n.path.split('/').pop().split('::').pop()
      })),
      links
    };
  }, [rawNodes, rawEdges, moduleFilter, kindFilter, maxNodes, searchQuery]);

  // Initialize ForceGraph3D
  useEffect(() => {
    if (!mountRef.current) return;

    // Clean previous DOM if any
    mountRef.current.innerHTML = '';

    const graph = ForceGraph3D()(mountRef.current)
      .backgroundColor('#070a13')
      .nodeId('id')
      .nodeLabel(node => `
        <div style="background: rgba(11, 16, 28, 0.95); padding: 8px 12px; border-radius: 6px; border: 1px solid #38bdf8; font-family: monospace; font-size: 11px; color: #fff; max-width: 320px; box-shadow: 0 4px 18px rgba(0,0,0,0.5);">
          <strong style="color: #38bdf8; font-size: 12px;">${node.name}</strong><br/>
          <span style="color: #94a3b8; word-break: break-all;">${node.path}</span><br/>
          <div style="margin-top: 4px; display: flex; gap: 6px;">
            <span style="color: #10b981;">Kind: ${node.kind || node.level || 'node'}</span>
            ${node.language ? `<span style="color: #a855f7;">[${node.language}]</span>` : ''}
          </div>
        </div>
      `)
      .nodeColor(node => {
        if (selectedNode && selectedNode.path === node.id) {
          return '#38bdf8'; // Glowing cyan for selected
        }
        return getNodeColor(node);
      })
      .nodeRelSize(5)
      .nodeVal(node => {
        const k = (node.kind || node.level || '').toLowerCase();
        if (k === 'class' || k === 'interface') return 8;
        if (k === 'file') return 6;
        return 4;
      })
      .linkDirectionalParticles(2)
      .linkDirectionalParticleSpeed(0.005)
      .linkDirectionalParticleWidth(1.4)
      .linkColor(link => {
        if (link.edge_type === 'calls') return 'rgba(56, 189, 248, 0.45)';
        if (link.edge_type === 'imports') return 'rgba(168, 85, 247, 0.4)';
        return 'rgba(100, 116, 139, 0.3)';
      })
      .linkOpacity(0.28)
      .onNodeClick(node => {
        // Aim camera smoothly at node
        const distance = 90;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
        graph.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node,
          1500
        );
        if (onSelectNode) onSelectNode(node);
      })
      .showNavInfo(false);

    graphInstanceRef.current = graph;

    // Handle container resize
    const handleResize = () => {
      if (mountRef.current && graphInstanceRef.current) {
        graphInstanceRef.current.width(mountRef.current.clientWidth);
        graphInstanceRef.current.height(mountRef.current.clientHeight);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (mountRef.current) {
        mountRef.current.innerHTML = '';
      }
    };
  }, []);

  // Update graph data when filteredData changes
  useEffect(() => {
    if (graphInstanceRef.current && filteredGraphData) {
      graphInstanceRef.current.graphData(filteredGraphData);
    }
  }, [filteredGraphData]);

  // Handle selected node highlight
  useEffect(() => {
    if (graphInstanceRef.current) {
      graphInstanceRef.current.nodeColor(node => {
        if (selectedNode && selectedNode.path === node.id) {
          return '#38bdf8';
        }
        return getNodeColor(node);
      });
    }
  }, [selectedNode]);

  const handleResetCamera = () => {
    if (graphInstanceRef.current) {
      graphInstanceRef.current.cameraPosition({ x: 0, y: 0, z: 450 }, { x: 0, y: 0, z: 0 }, 1200);
    }
    if (onResetCamera) onResetCamera();
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#070a13' }}>
      {/* 3D WebGL Canvas Mounting Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating 3D Control Bar & Filters */}
      <div style={{ 
        position: 'absolute', 
        top: 14, 
        left: 14, 
        zIndex: 20, 
        display: 'flex', 
        gap: 8, 
        alignItems: 'center', 
        flexWrap: 'wrap',
        background: 'rgba(11, 16, 28, 0.85)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 10,
        padding: '8px 12px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Module Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <select 
            value={moduleFilter} 
            onChange={(e) => setModuleFilter(e.target.value)}
            style={{ 
              background: '#0f172a', 
              color: '#cbd5e1', 
              border: '1px solid var(--border-subtle)', 
              borderRadius: 6, 
              padding: '4px 8px', 
              fontSize: 11.5,
              outline: 'none'
            }}
          >
            <option value="all">All Modules ({rawNodes.length.toLocaleString()})</option>
            <option value="files">apps/files (Filesystem Core)</option>
            <option value="dav">apps/dav (WebDAV & CalDAV)</option>
            <option value="ocp">lib/public (OCP Interfaces)</option>
            <option value="private">lib/private (Core Services)</option>
          </select>
        </div>

        {/* Kind Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <select 
            value={kindFilter} 
            onChange={(e) => setKindFilter(e.target.value)}
            style={{ 
              background: '#0f172a', 
              color: '#cbd5e1', 
              border: '1px solid var(--border-subtle)', 
              borderRadius: 6, 
              padding: '4px 8px', 
              fontSize: 11.5,
              outline: 'none'
            }}
          >
            <option value="all">All Kinds</option>
            <option value="classes">Classes & Interfaces</option>
            <option value="methods">Methods & Routes</option>
            <option value="files">Files Only</option>
          </select>
        </div>

        {/* Max Nodes Limit */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Sliders className="w-3.5 h-3.5 text-emerald-400" />
          <select 
            value={maxNodes} 
            onChange={(e) => setMaxNodes(Number(e.target.value))}
            style={{ 
              background: '#0f172a', 
              color: '#cbd5e1', 
              border: '1px solid var(--border-subtle)', 
              borderRadius: 6, 
              padding: '4px 8px', 
              fontSize: 11.5,
              outline: 'none'
            }}
          >
            <option value={300}>300 Nodes (Ultra Fast)</option>
            <option value={600}>600 Nodes (Balanced 60 FPS)</option>
            <option value={1200}>1,200 Nodes (Detailed)</option>
            <option value={2500}>2,500 Nodes (Full Core)</option>
          </select>
        </div>

        {/* Camera Reset */}
        <button 
          onClick={handleResetCamera}
          title="Reset Orbit Camera"
          style={{ 
            background: 'rgba(255, 255, 255, 0.08)', 
            border: '1px solid var(--border-subtle)', 
            borderRadius: 6, 
            padding: '4px 8px', 
            color: '#e2e8f0', 
            fontSize: 11.5, 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4
          }}
        >
          <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Reset Camera</span>
        </button>
      </div>

      {/* 3D Navigation Controls Legend (Bottom Left) */}
      <div style={{ 
        position: 'absolute', 
        bottom: 14, 
        left: 14, 
        zIndex: 20, 
        background: 'rgba(11, 16, 28, 0.85)', 
        backdropFilter: 'blur(10px)', 
        border: '1px solid rgba(255, 255, 255, 0.08)', 
        borderRadius: 8, 
        padding: '8px 12px', 
        fontSize: 11, 
        color: '#94a3b8',
        display: 'flex',
        gap: 12
      }}>
        <span><strong style={{ color: '#38bdf8' }}>Left Drag:</strong> 3D Orbit</span>
        <span><strong style={{ color: '#818cf8' }}>Right Drag:</strong> Pan</span>
        <span><strong style={{ color: '#10b981' }}>Wheel:</strong> Infinite Zoom</span>
        <span><strong style={{ color: '#fbbf24' }}>Click Node:</strong> Fly & Inspect</span>
      </div>

      {/* Visible Node / Link Stats (Bottom Right) */}
      <div style={{ 
        position: 'absolute', 
        bottom: 14, 
        right: 14, 
        zIndex: 20, 
        background: 'rgba(11, 16, 28, 0.85)', 
        backdropFilter: 'blur(10px)', 
        border: '1px solid rgba(255, 255, 255, 0.08)', 
        borderRadius: 8, 
        padding: '8px 14px', 
        fontSize: 11, 
        fontFamily: 'var(--font-mono)',
        color: '#e2e8f0',
        display: 'flex',
        gap: 10,
        alignItems: 'center'
      }}>
        <span style={{ color: '#38bdf8' }}>{filteredGraphData.nodes.length} Nodes Rendered</span>
        <span style={{ color: '#64748b' }}>•</span>
        <span style={{ color: '#10b981' }}>{filteredGraphData.links.length} Active Edges</span>
        <span style={{ color: '#64748b' }}>•</span>
        <span style={{ color: '#a855f7' }}>60 FPS WebGL</span>
      </div>
    </div>
  );
}
