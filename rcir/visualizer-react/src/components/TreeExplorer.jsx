import React, { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Folder, File, Code, Box, Terminal, Search } from 'lucide-react';
import { getNodeColor } from '../lib/colors';

function TreeNodeItem({ item, level = 0, selectedNode, onSelectNode }) {
  const [expanded, setExpanded] = useState(level < 2);

  const hasChildren = item.children && item.children.length > 0;
  const isSelected = selectedNode && selectedNode.path === item.path;
  const color = getNodeColor(item);

  const getIcon = () => {
    switch (item.level) {
      case 'root': return <Box size={14} color={color} />;
      case 'module': return <Folder size={14} color={color} />;
      case 'file': return <File size={14} color={color} />;
      case 'class': return <Code size={14} color={color} />;
      case 'function': return <Terminal size={14} color={color} />;
      default: return <Code size={14} color={color} />;
    }
  };

  const displayName = item.path.split('::').pop().split('/').pop();

  return (
    <div style={{ userSelect: 'none' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '4px 6px',
          paddingLeft: `${Math.max(6, level * 14)}px`,
          borderRadius: 4,
          background: isSelected ? '#1e253b' : 'transparent',
          border: isSelected ? '1px solid #4f5b84' : '1px solid transparent',
          cursor: 'pointer',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          transition: 'background 0.1s ease'
        }}
        onClick={() => onSelectNode(item)}
      >
        {/* Toggle */}
        {hasChildren ? (
          <span
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            style={{ display: 'flex', alignItems: 'center', color: '#94a3b8' }}
          >
            {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </span>
        ) : (
          <span style={{ width: 13 }} />
        )}

        {/* Icon */}
        {getIcon()}

        {/* Name */}
        <span style={{
          color: isSelected ? '#ffffff' : '#e2e8f0',
          fontWeight: isSelected ? 700 : 400,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {displayName}
        </span>

        {/* Level */}
        <span style={{
          marginLeft: 'auto',
          fontSize: 9.5,
          color: '#94a3b8',
          textTransform: 'uppercase',
          fontWeight: 600
        }}>
          {item.level}
        </span>
      </div>

      {hasChildren && expanded && (
        <div>
          {item.children.map((child, idx) => (
            <TreeNodeItem
              key={child.path || idx}
              item={child}
              level={level + 1}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function TreeExplorer({ hierarchy, selectedNode, onSelectNode }) {
  const [filter, setFilter] = useState('');

  const treeData = useMemo(() => {
    if (!hierarchy?.nodes || hierarchy.nodes.length === 0) return [];

    const nodeMap = new Map();
    hierarchy.nodes.forEach(n => {
      nodeMap.set(n.path, { ...n, children: [] });
    });

    const roots = [];
    hierarchy.nodes.forEach(n => {
      const node = nodeMap.get(n.path);
      if (!n.parent || n.parent === n.path || !nodeMap.has(n.parent)) {
        roots.push(node);
      } else {
        nodeMap.get(n.parent).children.push(node);
      }
    });

    return roots;
  }, [hierarchy]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-app)',
      padding: '16px 20px',
      overflow: 'hidden'
    }}>
      <div style={{ marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>Structural AST Hierarchy</h2>
        <p style={{ fontSize: 12, color: '#94a3b8' }}>
          Navigable function → class → file → module hierarchy tree (§4.2)
        </p>
      </div>

      {/* Filter Input */}
      <div style={{ position: 'relative', marginBottom: 10 }}>
        <Search size={14} style={{ position: 'absolute', left: 9, top: 9, color: '#94a3b8' }} />
        <input
          type="text"
          className="input-text"
          placeholder="Filter tree nodes..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ width: '100%', paddingLeft: 30, fontSize: 12 }}
        />
      </div>

      {/* Tree View */}
      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto', padding: 10 }}>
        {treeData.length === 0 ? (
          <div style={{ color: '#94a3b8', fontSize: 12.5, textAlign: 'center', marginTop: 40 }}>
            No hierarchy data loaded
          </div>
        ) : (
          treeData.map((root, idx) => (
            <TreeNodeItem
              key={root.path || idx}
              item={root}
              level={0}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
            />
          ))
        )}
      </div>
    </div>
  );
}
