import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ProofModal } from './components/ProofModal';
import { Tab01PolyFlow } from './components/Tab01PolyFlow';
import { Tab02Interpreter } from './components/Tab02Interpreter';
import { Tab03RCIR } from './components/Tab03RCIR';
import { Tab04Proofs } from './components/Tab04Proofs';
import { Tab05ERPNextScale } from './components/Tab05ERPNextScale';

import { useGraphData } from './hooks/useGraphData';
import { useCamera } from './hooks/useCamera';

export default function App() {
  const [activeTab, setActiveTab] = useState('polyflow');
  const [isProofModalOpen, setIsProofModalOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Keyboard shortcut Ctrl+B / Cmd+B to toggle sidebar collapse
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setIsSidebarCollapsed(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Primary Graph Data Hook (for Nextcloud AST graph exploration in Tab 03)
  const {
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

  return (
    <div className="app-container">
      {/* Left Navigation Sidebar (Exactly 5 Primary Tabs) */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(prev => !prev)}
      />

      {/* Main Viewport */}
      <main className="main-viewport" style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, height: '100vh', overflow: 'hidden' }}>
        {/* Top Header */}
        <Header
          currentDatasetId={datasetId}
          onSelectDataset={setDatasetId}
          onOpenProofModal={() => setIsProofModalOpen(true)}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(prev => !prev)}
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebarCollapse={() => setIsSidebarCollapsed(prev => !prev)}
        />

        {/* Viewport Content Area */}
        <div className="content-area" style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
          {activeTab === 'polyflow' && <Tab01PolyFlow />}
          {activeTab === 'interpreter' && <Tab02Interpreter />}
          {activeTab === 'rcir' && (
            <Tab03RCIR
              graphData={data}
              layout={layout}
              layoutMode={layoutMode}
              setLayoutMode={setLayoutMode}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
              hoveredNode={hoveredNode}
              setHoveredNode={setHoveredNode}
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
            />
          )}
          {(activeTab === 'proofs' || activeTab === 'agent') && <Tab04Proofs />}
          {activeTab === 'erpnext' && <Tab05ERPNextScale />}
        </div>
      </main>

      {/* Proof Modal */}
      <ProofModal
        isOpen={isProofModalOpen}
        onClose={() => setIsProofModalOpen(false)}
        currentDatasetId={datasetId}
        datasetInfo={{ name: datasetId }}
      />
    </div>
  );
}
