import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { GraphCanvas } from './components/GraphCanvas';
import { NodeInspector } from './components/NodeInspector';
import { TreeExplorer } from './components/TreeExplorer';
import { RetrievalSimulator } from './components/RetrievalSimulator';
import { BenchmarkArena } from './components/BenchmarkArena';
import { AgentPipeline } from './components/AgentPipeline';
import { ExecutiveHero } from './components/ExecutiveHero';
import { PolyglotStudio } from './components/PolyglotStudio';
import { ProofCenter } from './components/ProofCenter';
import { ProofModal } from './components/ProofModal';
import { StatsBar } from './components/StatsBar';

import { useGraphData } from './hooks/useGraphData';
import { useCamera } from './hooks/useCamera';
import { useAgent } from './hooks/useAgent';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isProofModalOpen, setIsProofModalOpen] = useState(false);
  const [manifest, setManifest] = useState([]);

  // Load Manifest
  useEffect(() => {
    fetch('/data/manifest.json')
      .then(res => res.json())
      .then(data => setManifest(data))
      .catch(err => console.warn('Could not load manifest.json', err));
  }, []);

  // Primary Graph Data Hook
  const {
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
  } = useGraphData('nextcloud');

  // Camera Hook
  const {
    camera,
    setCamera,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    zoomIn,
    zoomOut,
    resetCamera
  } = useCamera(1, 0, 0);

  // Agent Pipeline Hook
  const agentState = useAgent(datasetId, data?.graph?.nodes || []);

  const totalNodes = data?.graph?.nodes?.length || 0;
  const totalEdges = data?.graph?.edges?.length || 0;
  const datasetInfo = manifest.find(m => m.id === datasetId) || { name: datasetId };

  // Handler when agent pipeline requests highlighting nodes on graph
  const handleHighlightTouchedNodes = (nodePaths) => {
    setHighlightedNodes(new Set(nodePaths));
    setActiveTab('graph');
  };

  return (
    <div className="app-container">
      {/* Left Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        datasetInfo={datasetInfo}
        nodeCount={totalNodes}
        edgeCount={totalEdges}
      />

      {/* Main Viewport */}
      <main className="main-viewport">
        {/* Top Header */}
        <Header
          manifest={manifest}
          currentDatasetId={datasetId}
          onSelectDataset={setDatasetId}
          layoutMode={layoutMode}
          onToggleLayout={setLayoutMode}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onResetCamera={resetCamera}
          onOpenProofModal={() => setIsProofModalOpen(true)}
          totalNodes={totalNodes}
          totalEdges={totalEdges}
        />

        {/* Viewport Content Area */}
        <div className="content-area">
          {loading ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
              <div className="pulse-node" style={{ width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)' }} />
              <div style={{ color: 'var(--text-secondary)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
                Extracting AST dependency graph for {datasetId}...
              </div>
            </div>
          ) : error ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <div style={{ color: '#fb7185', fontSize: 16, fontWeight: 600 }}>Error loading dataset</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{error}</div>
            </div>
          ) : (
            <>
              {/* Tab 0: Executive Overview */}
              {activeTab === 'overview' && (
                <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
                  <ExecutiveHero onNavigate={setActiveTab} />
                </div>
              )}

              {/* Tab 1: Obsidian Graph Canvas */}
              {activeTab === 'graph' && (
                <div style={{ flex: 1, position: 'relative', height: '100%' }}>
                  <GraphCanvas
                    layout={layout}
                    selectedNode={selectedNode}
                    onSelectNode={setSelectedNode}
                    hoveredNode={hoveredNode}
                    onHoverNode={setHoveredNode}
                    connectedNeighbors={connectedNeighbors}
                    highlightedNodes={highlightedNodes}
                    searchQuery={searchQuery}
                    matchingNodePaths={matchingNodePaths}
                    camera={camera}
                    setCamera={setCamera}
                    handleWheel={handleWheel}
                    handleMouseDown={handleMouseDown}
                    handleMouseMove={handleMouseMove}
                    handleMouseUp={handleMouseUp}
                    zoomIn={zoomIn}
                    zoomOut={zoomOut}
                    resetCamera={resetCamera}
                    layoutMode={layoutMode}
                    onToggleLayout={setLayoutMode}
                  />

                  {/* Right Slide-out Inspector */}
                  {selectedNode && (
                    <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, zIndex: 25 }}>
                      <NodeInspector
                        node={selectedNode}
                        graphData={data}
                        onClose={() => setSelectedNode(null)}
                        onSelectNodeByPath={selectNodeByPath}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Tree Explorer */}
              {activeTab === 'tree' && (
                <div style={{ flex: 1, display: 'flex', height: '100%', position: 'relative' }}>
                  <TreeExplorer
                    hierarchy={data?.hierarchy}
                    selectedNode={selectedNode}
                    onSelectNode={(node) => {
                      setSelectedNode(node);
                      selectNodeByPath(node.path);
                    }}
                  />
                  {selectedNode && (
                    <NodeInspector
                      node={selectedNode}
                      graphData={data}
                      onClose={() => setSelectedNode(null)}
                      onSelectNodeByPath={selectNodeByPath}
                    />
                  )}
                </div>
              )}

              {/* Tab 3: Retrieval Simulator */}
              {activeTab === 'retrieval' && (
                <RetrievalSimulator
                  graphData={data}
                  datasetId={datasetId}
                  onSelectNode={(node) => {
                    selectNodeByPath(node.path);
                    setActiveTab('graph');
                  }}
                />
              )}

              {/* Tab 4: Benchmark Arena */}
              {activeTab === 'benchmarks' && (
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <BenchmarkArena />
                </div>
              )}

              {/* Tab 5: Agent Pipeline */}
              {activeTab === 'agent' && (
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <AgentPipeline
                    agentState={agentState}
                    onRunPipeline={agentState.runPipeline}
                    onCancelPipeline={agentState.cancelPipeline}
                    currentRepoName={datasetId}
                    onHighlightTouchedNodes={handleHighlightTouchedNodes}
                  />
                </div>
              )}

              {/* Tab 6: Polyglot Studio */}
              {activeTab === 'studio' && (
                <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
                  <PolyglotStudio />
                </div>
              )}

              {/* Tab 7: Proof & Audit Center */}
              {activeTab === 'proof' && (
                <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
                  <ProofCenter />
                </div>
              )}
            </>
          )}
        </div>

        {/* Bottom HUD Stats Bar */}
        <StatsBar
          datasetId={datasetId}
          nodeCount={totalNodes}
          edgeCount={totalEdges}
          layoutMode={layoutMode}
          zoomScale={camera.scale}
          selectedNode={selectedNode}
        />
      </main>

      {/* Proof Modal */}
      <ProofModal
        isOpen={isProofModalOpen}
        onClose={() => setIsProofModalOpen(false)}
        currentDatasetId={datasetId}
        datasetInfo={datasetInfo}
      />
    </div>
  );
}
