/**
 * Color palette and level definitions for RCIR Visualizer.
 */

export const LEVEL_COLORS = {
  root: '#a855f7',     // Purple
  module: '#06b6d4',   // Cyan
  file: '#3b82f6',     // Blue
  class: '#f59e0b',    // Amber
  function: '#10b981', // Emerald
  unknown: '#94a3b8'   // Slate
};

export const AGENT_COLORS = {
  maker: '#ec4899',       // Pink / Magenta
  reviewer: '#3b82f6',    // Blue
  implementer: '#10b981', // Emerald
  gatekeeper: '#f59e0b',  // Amber
  historian: '#8b5cf6'    // Purple
};

export const EDGE_COLORS = {
  calls: '#6366f1',
  imports: '#06b6d4',
  inherits: '#f59e0b',
  contains: '#475569',
  default: '#64748b'
};

export function getNodeColor(node) {
  if (!node) return LEVEL_COLORS.unknown;
  const level = (node.level || node.kind || '').toLowerCase();
  return LEVEL_COLORS[level] || LEVEL_COLORS.unknown;
}

export function hexToRgba(hex, alpha = 1) {
  const cleanHex = hex.replace('#', '');
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
