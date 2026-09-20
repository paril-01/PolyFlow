import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Plus, Minus, Maximize2, RefreshCw, Filter, Compass, GitBranch, Layers } from 'lucide-react';
import { getNodeColor, hexToRgba, EDGE_COLORS } from '../lib/colors';
import { computeBoundsAndFit } from '../lib/graphLayout';

// Helper: Draw directional arrowhead
function drawArrowhead(ctx, fromX, fromY, toX, toY, targetRadius, color, size = 6.5) {
  const dx = toX - fromX;
  const dy = toY - fromY;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < targetRadius + size) return;

  const ux = dx / dist;
  const uy = dy / dist;

  // Arrow tip touches the outer edge of target node
  const tipX = toX - ux * (targetRadius + 2);
  const tipY = toY - uy * (targetRadius + 2);

  const leftX = tipX - ux * size - uy * (size * 0.55);
  const leftY = tipY - uy * size + ux * (size * 0.55);

  const rightX = tipX - ux * size + uy * (size * 0.55);
  const rightY = tipY - uy * size - ux * (size * 0.55);

  ctx.beginPath();
  ctx.moveTo(tipX, tipY);
  ctx.lineTo(leftX, leftY);
  ctx.lineTo(rightX, rightY);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

// Helper: Draw rounded pill background
function drawPillBackground(ctx, x, y, width, height, radius, fill, stroke) {
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fillStyle = fill;
  ctx.fill();
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

export function GraphCanvas({
  layout,
  selectedNode,
  onSelectNode,
  hoveredNode,
  onHoverNode,
  connectedNeighbors,
  highlightedNodes,
  searchQuery,
  matchingNodePaths,
  camera,
  setCamera,
  handleWheel,
  handleMouseDown,
  handleMouseMove,
  handleMouseUp,
  zoomIn,
  zoomOut,
  resetCamera,
  layoutMode,
  onToggleLayout
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 1200, height: 700 });
  const [tooltip, setTooltip] = useState(null);
  const [edgeFilter, setEdgeFilter] = useState('all'); // 'all' | 'calls' | 'imports'
  const rafId = useRef(null);

  // Resize canvas
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        if (clientWidth > 0 && clientHeight > 0) {
          setCanvasSize({ width: clientWidth, height: clientHeight });
        }
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Zoom to Fit Helper
  const handleZoomToFit = useCallback(() => {
    if (!layout?.nodes || layout.nodes.length === 0) return;
    const fit = computeBoundsAndFit(layout.nodes, canvasSize.width, canvasSize.height);
    setCamera({ x: fit.x, y: fit.y, scale: fit.scale });
  }, [layout, canvasSize, setCamera]);

  // Trigger Zoom to Fit on layout change or initial data load
  useEffect(() => {
    if (layout?.nodes && layout.nodes.length > 0) {
      handleZoomToFit();
    }
  }, [layoutMode, layout?.nodes?.length]);

  // High-Performance Render Loop
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const { width, height } = canvasSize;

    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }
    ctx.resetTransform();
    ctx.scale(dpr, dpr);

    // Dark solid canvas background
    ctx.fillStyle = '#0a0c12';
    ctx.fillRect(0, 0, width, height);

    ctx.save();
    // Camera Transform (Centered)
    ctx.translate(width / 2 + camera.x, height / 2 + camera.y);
    ctx.scale(camera.scale, camera.scale);
    ctx.translate(-width / 2, -height / 2);

    const { nodes = [], links = [] } = layout;

    // 1. BACKGROUND GUIDES
    if (layoutMode === 'flow') {
      // Flow DAG Columns Guide Headers
      const colHeaders = [
        { label: 'ROOT PACKAGE', x: 80, color: '#c084fc' },
        { label: 'MODULES', x: 320, color: '#22d3ee' },
        { label: 'SOURCE FILES', x: 600, color: '#60a5fa' },
        { label: 'CLASSES', x: 880, color: '#fbbf24' },
        { label: 'FUNCTIONS / METHODS', x: 1180, color: '#34d399' }
      ];

      colHeaders.forEach(col => {
        // Vertical dashed column guide line
        ctx.beginPath();
        ctx.moveTo(col.x, 30);
        ctx.lineTo(col.x, height * 1.5);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.setLineDash([4, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Column Header Label
        ctx.fillStyle = col.color;
        ctx.font = 'bold 11px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(col.label, col.x, 40);
      });
    } else if (layoutMode === 'radial') {
      // Concentric Rings
      const centerX = width / 2;
      const centerY = height / 2;
      const maxR = layout.maxRadius || Math.min(width, height) * 0.4;
      const rings = [
        { r: maxR * 0.28, label: 'MODULES', color: '#22d3ee' },
        { r: maxR * 0.52, label: 'FILES', color: '#60a5fa' },
        { r: maxR * 0.76, label: 'CLASSES', color: '#fbbf24' },
        { r: maxR * 1.0, label: 'FUNCTIONS', color: '#34d399' }
      ];

      rings.forEach(ring => {
        ctx.beginPath();
        ctx.arc(centerX, centerY, ring.r, 0, 2 * Math.PI);
        ctx.strokeStyle = ring.color + '30';
        ctx.setLineDash([3, 5]);
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = ring.color + '90';
        ctx.font = '10px "JetBrains Mono", monospace';
        ctx.fillText(ring.label, centerX + 12, centerY - ring.r + 14);
      });
    }

    // 2. FILTER & DRAW EDGES
    const filteredLinks = links.filter(l => {
      if (edgeFilter === 'calls') return l.edge_type === 'calls';
      if (edgeFilter === 'imports') return l.edge_type === 'imports';
      return true;
    });

    // Draw normal & dimmed edges
    filteredLinks.forEach(link => {
      const s = link.source;
      const t = link.target;
      if (!s || !t || s.x === undefined || t.x === undefined) return;

      const isConnected = !connectedNeighbors || (connectedNeighbors.has(s.path) && connectedNeighbors.has(t.path));
      const isSelectedIncoming = selectedNode && t.path === selectedNode.path;
      const isSelectedOutgoing = selectedNode && s.path === selectedNode.path;

      // Color and stroke based on state
      let color = '#818cf8'; // default calls
      if (link.edge_type === 'imports') color = '#22d3ee';
      else if (link.edge_type === 'inherits') color = '#fbbf24';

      let alpha = 0.55;
      let width = 1.3;

      if (connectedNeighbors && !isConnected) {
        alpha = 0.05;
        width = 0.6;
      } else if (isSelectedIncoming) {
        color = '#34d399'; // Incoming callers = bright emerald
        alpha = 1.0;
        width = 2.4;
      } else if (isSelectedOutgoing) {
        color = '#38bdf8'; // Outgoing calls = bright cyan
        alpha = 1.0;
        width = 2.4;
      }

      ctx.beginPath();
      if (layoutMode === 'flow') {
        // Smooth horizontal S-curve (cubic Bezier) between columns
        const dx = (t.x - s.x) * 0.5;
        ctx.moveTo(s.x, s.y);
        ctx.bezierCurveTo(s.x + dx, s.y, t.x - dx, t.y, t.x, t.y);
      } else {
        // Organic curve
        ctx.moveTo(s.x, s.y);
        const midX = (s.x + t.x) / 2 + (s.y - t.y) * 0.05;
        const midY = (s.y + t.y) / 2 + (t.x - s.x) * 0.05;
        ctx.quadraticCurveTo(midX, midY, t.x, t.y);
      }

      ctx.strokeStyle = hexToRgba(color, alpha);
      ctx.lineWidth = width;
      ctx.stroke();

      // Draw Arrowhead if link is visible
      if (alpha > 0.25) {
        drawArrowhead(ctx, s.x, s.y, t.x, t.y, t.radius || 6, hexToRgba(color, alpha));
      }
    });

    // 3. DRAW NODES & READABLE LABEL PILLS
    nodes.forEach(node => {
      if (node.x === undefined || node.y === undefined) return;

      const isSelected = selectedNode && selectedNode.path === node.path;
      const isHovered = hoveredNode && hoveredNode.path === node.path;
      const isNeighbor = connectedNeighbors && connectedNeighbors.has(node.path);
      const isHighlighted = highlightedNodes && highlightedNodes.has(node.path);
      const isSearchMatch = matchingNodePaths && matchingNodePaths.has(node.path);

      let alpha = 1.0;
      if (connectedNeighbors && !isNeighbor) {
        alpha = 0.08;
      }
      if (matchingNodePaths && !isSearchMatch) {
        alpha = Math.min(alpha, 0.15);
      }

      const baseColor = getNodeColor(node);
      const r = (node.radius || 7) * (isSelected ? 1.4 : isHovered ? 1.25 : 1);

      // Glowing Outer Ring for Selected / Highlighted
      if (isSelected || isHighlighted || isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + (isSelected ? 10 : 6), 0, 2 * Math.PI);
        ctx.fillStyle = hexToRgba(isSelected ? '#818cf8' : baseColor, 0.35);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(node.x, node.y, r + (isSelected ? 5 : 3), 0, 2 * Math.PI);
        ctx.strokeStyle = isSelected ? '#ffffff' : baseColor;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Main Node Orb
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
      ctx.fillStyle = hexToRgba(baseColor, alpha);
      ctx.fill();

      // White Inner Core
      ctx.beginPath();
      ctx.arc(node.x, node.y, Math.max(2, r * 0.4), 0, 2 * Math.PI);
      ctx.fillStyle = hexToRgba('#ffffff', Math.min(1.0, alpha * 0.95));
      ctx.fill();

      // 4. READABLE LABEL PILL (Always readable on top of connections)
      if (alpha > 0.3) {
        const shortName = node.path.split('::').pop().split('/').pop();
        ctx.font = `${isSelected ? 'bold 12px' : '11px'} "Inter", sans-serif`;
        const textMetrics = ctx.measureText(shortName);
        const pillWidth = textMetrics.width + 12;
        const pillHeight = 18;

        let pillX = node.x - pillWidth / 2;
        let pillY = node.y + r + 5;

        // In Flow DAG mode, position label to the right of node
        if (layoutMode === 'flow') {
          pillX = node.x + r + 6;
          pillY = node.y - pillHeight / 2;
        }

        // Draw pill background
        const pillBg = isSelected ? '#1e263d' : '#10131d';
        const pillBorder = isSelected ? '#818cf8' : hexToRgba(baseColor, 0.4);
        drawPillBackground(ctx, pillX, pillY, pillWidth, pillHeight, 4, pillBg, pillBorder);

        // Draw text
        ctx.fillStyle = isSelected ? '#ffffff' : '#f8fafc';
        ctx.textAlign = 'left';
        ctx.fillText(shortName, pillX + 6, pillY + 13);
      }
    });

    ctx.restore();
  }, [layout, selectedNode, hoveredNode, connectedNeighbors, highlightedNodes, matchingNodePaths, camera, canvasSize, layoutMode, edgeFilter]);

  // RequestAnimationFrame
  useEffect(() => {
    rafId.current = requestAnimationFrame(renderCanvas);
    return () => cancelAnimationFrame(rafId.current);
  }, [renderCanvas]);

  // Fast Throttled MouseMove
  const onCanvasMouseMove = useCallback((e) => {
    handleMouseMove(e);

    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const { width, height } = canvasSize;
    const graphX = (clientX - (width / 2 + camera.x)) / camera.scale + width / 2;
    const graphY = (clientY - (height / 2 + camera.y)) / camera.scale + height / 2;

    const { nodes = [] } = layout;
    let found = null;
    const maxDist = 24 / camera.scale;
    const maxDistSq = maxDist * maxDist;

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (node.x === undefined || node.y === undefined) continue;
      const dx = node.x - graphX;
      const dy = node.y - graphY;
      if (dx * dx + dy * dy < maxDistSq) {
        found = node;
        break;
      }
    }

    if (found) {
      onHoverNode(found);
      setTooltip({
        x: e.clientX,
        y: e.clientY,
        node: found
      });
    } else {
      if (hoveredNode) onHoverNode(null);
      if (tooltip) setTooltip(null);
    }
  }, [camera, canvasSize, handleMouseMove, layout, onHoverNode, hoveredNode, tooltip]);

  // Click on Canvas
  const onCanvasClick = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const { width, height } = canvasSize;
    const graphX = (clientX - (width / 2 + camera.x)) / camera.scale + width / 2;
    const graphY = (clientY - (height / 2 + camera.y)) / camera.scale + height / 2;

    const { nodes = [] } = layout;
    let found = null;
    const maxDist = 26 / camera.scale;
    const maxDistSq = maxDist * maxDist;

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (node.x === undefined || node.y === undefined) continue;
      const dx = node.x - graphX;
      const dy = node.y - graphY;
      if (dx * dx + dy * dy < maxDistSq) {
        found = node;
        break;
      }
    }

    onSelectNode(found || null);
  }, [camera, canvasSize, layout, onSelectNode]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', cursor: 'grab' }}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={onCanvasMouseMove}
      onMouseUp={handleMouseUp}
      onClick={onCanvasClick}
    >
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />

      {/* Floating Canvas Usability Controls (Bottom-Right HUD) */}
      <div style={{
        position: 'absolute',
        right: 18,
        bottom: 18,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        background: '#121522',
        border: '1px solid #2d354e',
        borderRadius: 8,
        padding: '4px 8px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
        zIndex: 40
      }}>
        {/* Edge Filter Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginRight: 6, borderRight: '1px solid #283049', paddingRight: 8 }}>
          <Filter size={12} color="#94a3b8" />
          <button
            onClick={() => setEdgeFilter('all')}
            style={{
              background: edgeFilter === 'all' ? '#252d45' : 'transparent',
              border: 'none',
              color: edgeFilter === 'all' ? '#fff' : '#94a3b8',
              borderRadius: 4,
              padding: '3px 6px',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            All
          </button>
          <button
            onClick={() => setEdgeFilter('calls')}
            style={{
              background: edgeFilter === 'calls' ? '#818cf835' : 'transparent',
              border: `1px solid ${edgeFilter === 'calls' ? '#818cf8' : 'transparent'}`,
              color: edgeFilter === 'calls' ? '#818cf8' : '#94a3b8',
              borderRadius: 4,
              padding: '2px 6px',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Calls
          </button>
          <button
            onClick={() => setEdgeFilter('imports')}
            style={{
              background: edgeFilter === 'imports' ? '#22d3ee35' : 'transparent',
              border: `1px solid ${edgeFilter === 'imports' ? '#22d3ee' : 'transparent'}`,
              color: edgeFilter === 'imports' ? '#22d3ee' : '#94a3b8',
              borderRadius: 4,
              padding: '2px 6px',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Imports
          </button>
        </div>

        {/* Zoom Controls */}
        <button className="btn-icon" onClick={zoomIn} title="Zoom In">
          <Plus size={14} />
        </button>
        <button className="btn-icon" onClick={zoomOut} title="Zoom Out">
          <Minus size={14} />
        </button>
        <button className="btn-icon" onClick={handleZoomToFit} title="Zoom to Fit Screen">
          <Maximize2 size={13} />
        </button>
      </div>

      {/* Floating Layout Switcher (Top-Left overlay inside canvas) */}
      <div style={{
        position: 'absolute',
        left: 18,
        top: 18,
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        background: '#121522',
        border: '1px solid #2d354e',
        borderRadius: 8,
        padding: 3,
        boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
        zIndex: 40
      }}>
        <button
          onClick={() => onToggleLayout('flow')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '5px 10px',
            borderRadius: 6,
            fontSize: 11.5,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: layoutMode === 'flow' ? '#27304d' : 'transparent',
            color: layoutMode === 'flow' ? '#ffffff' : '#94a3b8'
          }}
          title="Hierarchical Architecture Flow (Module -> File -> Class -> Function)"
        >
          <Layers size={13} color={layoutMode === 'flow' ? '#818cf8' : 'currentColor'} />
          <span>Flow (DAG)</span>
        </button>

        <button
          onClick={() => onToggleLayout('radial')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '5px 10px',
            borderRadius: 6,
            fontSize: 11.5,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: layoutMode === 'radial' ? '#27304d' : 'transparent',
            color: layoutMode === 'radial' ? '#ffffff' : '#94a3b8'
          }}
          title="Adaptive Concentric Radial Rings"
        >
          <Compass size={13} color={layoutMode === 'radial' ? '#22d3ee' : 'currentColor'} />
          <span>Radial</span>
        </button>

        <button
          onClick={() => onToggleLayout('force')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '5px 10px',
            borderRadius: 6,
            fontSize: 11.5,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: layoutMode === 'force' ? '#27304d' : 'transparent',
            color: layoutMode === 'force' ? '#ffffff' : '#94a3b8'
          }}
          title="Force Cluster Network"
        >
          <GitBranch size={13} color={layoutMode === 'force' ? '#fbbf24' : 'currentColor'} />
          <span>Force</span>
        </button>
      </div>

      {/* Rich Node Hover Card */}
      {tooltip && (
        <div
          style={{
            position: 'fixed',
            left: tooltip.x + 14,
            top: tooltip.y + 14,
            background: '#141826',
            border: '1px solid #3d4668',
            borderRadius: 6,
            padding: '8px 12px',
            pointerEvents: 'none',
            zIndex: 100,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.75)',
            maxWidth: 360
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: getNodeColor(tooltip.node) }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#ffffff', textTransform: 'uppercase' }}>
              {tooltip.node.level || tooltip.node.kind}
            </span>
            {tooltip.node.line && (
              <span style={{ fontSize: 10.5, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                L{tooltip.node.line}-{tooltip.node.end_line || tooltip.node.line}
              </span>
            )}
          </div>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
            {tooltip.node.path}
          </div>
          {tooltip.node.hub_score && (
            <div style={{ fontSize: 11, color: '#e2e8f0', marginTop: 4 }}>
              Hub Centrality: <strong style={{ color: '#fbbf24' }}>{(tooltip.node.hub_score * 100).toFixed(1)}%</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
