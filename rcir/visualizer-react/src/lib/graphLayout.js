/**
 * High-Readability Layout Algorithms for RCIR Visualizer:
 * 1. Architectural File Cluster Flow (Compact, clean DAG tree)
 * 2. Adaptive Radial Concentric Tree (Dynamic viewport radius)
 * 3. Force-Directed Network with proper hierarchy links
 */

import * as d3 from 'd3';

/**
 * Helper to build resolved links from both hierarchy ancestors and graph call edges.
 */
function extractAndResolveLinks(rawNodes, rawEdges, hierarchyNodes) {
  const nodeMap = new Map();
  const symMap = new Map();

  rawNodes.forEach(n => {
    nodeMap.set(n.path, n);
    const sym = n.path.split('::').pop();
    if (sym) symMap.set(sym, n.path);
  });

  const links = [];
  const seen = new Set();

  // 1. Hierarchy Parent-Child Links (structural edges connecting the tree)
  (hierarchyNodes || []).forEach(n => {
    const parentPath = (n.ancestors && n.ancestors.length > 0) ? n.ancestors[0] : n.parent;
    if (parentPath && nodeMap.has(parentPath) && nodeMap.has(n.path) && parentPath !== n.path) {
      const key = `${parentPath}->${n.path}`;
      if (!seen.has(key)) {
        seen.add(key);
        links.push({
          source: parentPath,
          target: n.path,
          edge_type: 'contains',
          confidence: 1.0
        });
      }
    }
  });

  // 2. Graph Call / Import / Inherits Links
  (rawEdges || []).forEach(e => {
    let targetPath = null;
    if (nodeMap.has(e.target)) {
      targetPath = e.target;
    } else if (symMap.has(e.target)) {
      targetPath = symMap.get(e.target);
    } else {
      const lastPart = e.target.split('.').pop();
      if (symMap.has(lastPart)) {
        targetPath = symMap.get(lastPart);
      }
    }

    if (targetPath && nodeMap.has(e.source) && e.source !== targetPath) {
      const key = `${e.source}->${targetPath}`;
      if (!seen.has(key)) {
        seen.add(key);
        links.push({
          source: e.source,
          target: targetPath,
          edge_type: e.type || e.edge_type || 'calls',
          confidence: e.confidence || 0.8
        });
      }
    }
  });

  return links;
}

/**
 * 1. ARCHITECTURAL HIERARCHICAL FLOW
 * Groups nodes compactly by File/Module with 3 clean columns:
 * Col 1: Root / Modules (x = 100)
 * Col 2: Source Files (x = 420)
 * Col 3: Classes & Key Functions (x = 820)
 * Col 4: Leaf Methods (x = 1200)
 * Prevents vertical sprawl so zoom stays at ~85-100% and labels are crystal clear.
 */
export function computeHierarchicalFlowLayout(data, width = 1200, height = 650) {
  const rawNodes = data?.hierarchy?.nodes || data?.graph?.nodes || [];
  if (rawNodes.length === 0) return { nodes: [], links: [] };

  const nodeMap = new Map();
  const rawLinks = extractAndResolveLinks(data?.graph?.nodes || rawNodes, data?.graph?.edges || [], data?.hierarchy?.nodes);

  // Group nodes by file
  const files = [];
  const rootNodes = [];
  const fileChildren = new Map();

  rawNodes.forEach(n => {
    const lvl = (n.level || n.kind || '').toLowerCase();
    if (lvl === 'root' || n.path === '.') {
      rootNodes.push(n);
    } else if (lvl === 'file' || (!n.path.includes('::') && n.path.endsWith('.py'))) {
      files.push(n);
      fileChildren.set(n.path, []);
    }
  });

  rawNodes.forEach(n => {
    const lvl = (n.level || n.kind || '').toLowerCase();
    if (lvl !== 'root' && lvl !== 'file' && n.path !== '.') {
      const filePath = (n.ancestors && n.ancestors.length > 0) ? n.ancestors[0] : (n.path.includes('::') ? n.path.split('::')[0] : null);
      if (filePath && fileChildren.has(filePath)) {
        fileChildren.get(filePath).push(n);
      } else if (files.length > 0) {
        fileChildren.get(files[0].path)?.push(n);
      }
    }
  });

  const layoutNodes = [];
  let currentY = 50;

  // Position Root
  if (rootNodes.length > 0) {
    const r = rootNodes[0];
    const rootNode = { ...r, x: 80, y: height / 2, radius: 14 };
    nodeMap.set(r.path, rootNode);
    layoutNodes.push(rootNode);
  }

  // Layout each file cluster
  files.forEach((f, fIdx) => {
    const children = fileChildren.get(f.path) || [];
    const clusterHeight = Math.max(70, children.length * 28);
    const fileY = currentY + clusterHeight / 2;

    const fileNode = {
      ...f,
      x: 360,
      y: fileY,
      radius: 10
    };
    nodeMap.set(f.path, fileNode);
    layoutNodes.push(fileNode);

    // Layout children of this file
    children.forEach((child, cIdx) => {
      const childY = currentY + cIdx * 28 + 14;
      const isClass = (child.level || child.kind) === 'class';
      const childNode = {
        ...child,
        x: isClass ? 720 : 1060,
        y: childY,
        radius: isClass ? 8 : 6
      };
      nodeMap.set(child.path, childNode);
      layoutNodes.push(childNode);
    });

    currentY += clusterHeight + 40;
  });

  // Attach source and target node objects to links
  const layoutLinks = [];
  rawLinks.forEach(l => {
    const s = nodeMap.get(l.source);
    const t = nodeMap.get(l.target);
    if (s && t) {
      layoutLinks.push({ ...l, source: s, target: t });
    }
  });

  return { nodes: layoutNodes, links: layoutLinks };
}

/**
 * 2. ADAPTIVE RADIAL TREE LAYOUT
 * Fully connected concentric tree radiating from root to files to classes to methods.
 */
export function computeAdaptiveRadialLayout(hierarchy, width = 1200, height = 650) {
  const nodes = hierarchy?.nodes || [];
  if (nodes.length === 0) return { nodes: [], links: [] };

  const nodeMap = new Map();
  nodes.forEach(n => nodeMap.set(n.path, { ...n, children: [] }));

  // Find root node (path === '.' or level === 'root' or empty ancestors)
  let rootNode = null;
  for (const n of nodes) {
    if (n.path === '.' || n.level === 'root' || !n.ancestors || n.ancestors.length === 0) {
      rootNode = nodeMap.get(n.path);
      break;
    }
  }
  if (!rootNode && nodes.length > 0) rootNode = nodeMap.get(nodes[0].path);

  // Connect children using ancestors[0]
  nodes.forEach(n => {
    const parentPath = (n.ancestors && n.ancestors.length > 0) ? n.ancestors[0] : n.parent;
    if (parentPath && nodeMap.has(parentPath) && parentPath !== n.path) {
      nodeMap.get(parentPath).children.push(nodeMap.get(n.path));
    }
  });

  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = Math.min(width, height) * 0.42;

  try {
    const root = d3.hierarchy(rootNode);
    const cluster = d3.cluster().size([2 * Math.PI, maxRadius]);
    cluster(root);

    const layoutNodes = [];
    const layoutLinks = [];

    root.each(d => {
      const angle = d.x - Math.PI / 2;
      const radius = d.depth === 0 ? 0 : d.depth === 1 ? maxRadius * 0.35 : maxRadius * (0.35 + d.depth * 0.28);
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      const nodeObj = {
        ...d.data,
        x,
        y,
        radius: d.depth === 0 ? 14 : d.depth === 1 ? 10 : d.depth === 2 ? 8 : 6,
        depth: d.depth
      };
      nodeMap.set(d.data.path, nodeObj);
      layoutNodes.push(nodeObj);
    });

    root.links().forEach(link => {
      const s = nodeMap.get(link.source.data.path);
      const t = nodeMap.get(link.target.data.path);
      if (s && t) {
        layoutLinks.push({ source: s, target: t, edge_type: 'contains' });
      }
    });

    return { nodes: layoutNodes, links: layoutLinks, maxRadius };
  } catch (err) {
    console.warn('Radial tree calculation error', err);
    return { nodes: [], links: [] };
  }
}

/**
 * 3. FORCE NETWORK WITH STRONG REPULSION & HIERARCHY EDGES
 */
export function computeForceLayout(graphNodes, graphEdges, width = 1200, height = 650) {
  if (!graphNodes || graphNodes.length === 0) return { nodes: [], links: [] };

  const nodes = graphNodes.map(d => ({ ...d }));
  const nodeMap = new Map(nodes.map(n => [n.path, n]));
  const links = extractAndResolveLinks(graphNodes, graphEdges, graphNodes)
    .filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))
    .map(e => ({ ...e, source: nodeMap.get(e.source), target: nodeMap.get(e.target) }));

  const simulation = d3.forceSimulation(nodes)
    .force('charge', d3.forceManyBody().strength(-140))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('link', d3.forceLink(links).distance(60).strength(0.4))
    .force('collision', d3.forceCollide().radius(18))
    .stop();

  for (let i = 0; i < 140; ++i) simulation.tick();

  nodes.forEach(n => {
    n.radius = n.level === 'class' ? 9 : n.level === 'file' ? 8 : 6;
  });

  return { nodes, links };
}

/**
 * Compute optimal camera zoom and translation to fit all nodes inside canvas
 */
export function computeBoundsAndFit(nodes, canvasWidth, canvasHeight, padding = 40) {
  if (!nodes || nodes.length === 0 || canvasWidth <= 0 || canvasHeight <= 0) {
    return { scale: 0.9, x: 0, y: 0 };
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  nodes.forEach(n => {
    if (n.x === undefined || n.y === undefined) return;
    if (n.x < minX) minX = n.x;
    if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.y > maxY) maxY = n.y;
  });

  if (!isFinite(minX)) return { scale: 0.9, x: 0, y: 0 };

  const graphWidth = maxX - minX || 1;
  const graphHeight = maxY - minY || 1;

  const scaleX = (canvasWidth - padding * 2) / graphWidth;
  const scaleY = (canvasHeight - padding * 2) / graphHeight;
  // Keep scale between 0.65 and 1.1 so labels remain readable!
  const scale = Math.max(0.65, Math.min(1.1, Math.min(scaleX, scaleY)));

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const x = (canvasWidth / 2 - centerX) * scale;
  const y = (canvasHeight / 2 - centerY) * scale;

  return { scale, x, y };
}
