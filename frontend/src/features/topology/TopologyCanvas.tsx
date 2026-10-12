import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';

import { HostNode, HostGroupNode } from './HostNode';
import { NetworkNode } from './NetworkNode';
import { ContainerNode } from './ContainerNode';
import { TopologyInspectorDrawer, SelectedNodeDetails } from './TopologyInspectorDrawer';
import { ConnectHostModal } from './ConnectHostModal';

const nodeTypes = {
  hostNode: HostNode,
  hostGroupNode: HostGroupNode,
  networkNode: NetworkNode,
  containerNode: ContainerNode,
};

const AutoFitView: React.FC<{ filterKey: string }> = ({ filterKey }) => {
  const { fitView } = useReactFlow();

  useEffect(() => {
    const timer1 = setTimeout(() => {
      fitView({ padding: 0.2, duration: 200 });
    }, 50);
    const timer2 = setTimeout(() => {
      fitView({ padding: 0.2, duration: 200 });
    }, 250);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [filterKey, fitView]);

  return null;
};

const fetchTopology = async (envFilter: string, hostFilter: string) => {
  const params = new URLSearchParams();
  if (envFilter !== 'ALL') params.append('environment', envFilter);
  if (hostFilter !== 'ALL') params.append('host_id', hostFilter);

  const url = `/api/v1/topology${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch topology');
  return res.json();
};

const fetchHostsList = async () => {
  const res = await fetch('/api/v1/hosts');
  if (!res.ok) return [];
  return res.json();
};

const getLayoutedElements = (rawNodes: Node[], rawEdges: Edge[], layoutMode: string) => {
  if (layoutMode === 'tiered-3col') {
    const hosts = rawNodes.filter((n) => n.type === 'hostNode' || n.type === 'hostGroupNode');
    const networks = rawNodes.filter((n) => n.type === 'networkNode');
    const containers = rawNodes.filter((n) => n.type === 'containerNode');
    const others = rawNodes.filter((n) => !['hostNode', 'hostGroupNode', 'networkNode', 'containerNode'].includes(n.type || ''));

    const layoutedNodes = rawNodes.map((node) => {
      if (node.type === 'hostNode' || node.type === 'hostGroupNode') {
        const idx = hosts.findIndex((h) => h.id === node.id);
        return { ...node, position: { x: 40, y: 40 + idx * 160 } };
      } else if (node.type === 'networkNode') {
        const idx = networks.findIndex((n) => n.id === node.id);
        return { ...node, position: { x: 380, y: 40 + idx * 150 } };
      } else if (node.type === 'containerNode') {
        const idx = containers.findIndex((c) => c.id === node.id);
        return { ...node, position: { x: 740, y: 40 + idx * 120 } };
      } else {
        const idx = others.findIndex((o) => o.id === node.id);
        return { ...node, position: { x: 1060, y: 40 + idx * 120 } };
      }
    });

    return { nodes: layoutedNodes, edges: rawEdges };
  }

  if (layoutMode === 'grid') {
    const cols = Math.ceil(Math.sqrt(rawNodes.length));
    const layoutedNodes = rawNodes.map((node, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      return {
        ...node,
        position: {
          x: col * 260,
          y: row * 180,
        },
      };
    });
    return { nodes: layoutedNodes, edges: rawEdges };
  }

  const direction = layoutMode === 'dagre-LR' ? 'LR' : 'TB';
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 70, ranksep: 110 });

  rawNodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 220, height: 110 });
  });

  rawEdges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = rawNodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition ? nodeWithPosition.x - 110 : 0,
        y: nodeWithPosition ? nodeWithPosition.y - 55 : 0,
      },
    };
  });

  return { nodes: layoutedNodes, edges: rawEdges };
};

export const TopologyCanvas: React.FC = () => {
  const [envFilter, setEnvFilter] = useState('ALL');
  const [hostFilter, setHostFilter] = useState('ALL');
  const [driverFilter, setDriverFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [layoutMode, setLayoutMode] = useState<'tiered-3col' | 'dagre-TB' | 'dagre-LR' | 'grid'>('tiered-3col');
  const [enableFlowAnimation, setEnableFlowAnimation] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  const [selectedNode, setSelectedNode] = useState<SelectedNodeDetails | null>(null);

  const { data: hostsList } = useQuery({
    queryKey: ['hostsList'],
    queryFn: fetchHostsList,
  });

  const { data: topoData, isLoading, error, refetch } = useQuery({
    queryKey: ['topology', envFilter, hostFilter],
    queryFn: () => fetchTopology(envFilter, hostFilter),
    refetchInterval: 5000,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const processAndLayoutGraph = useCallback(() => {
    if (!topoData) return;

    let rawNodes: Node[] = (topoData.nodes || []).map((n: any) => {
      const copy = { ...n };
      delete copy.parentNode;
      return copy;
    });
    let rawEdges: Edge[] = topoData.edges || [];

    if (driverFilter !== 'ALL') {
      rawNodes = rawNodes.filter((n: any) => n.type !== 'networkNode' || n.data.driver === driverFilter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      rawNodes = rawNodes.filter((n: any) => n.data.label.toLowerCase().includes(term));
    }

    // Filter out dangling edges referencing non-existent node IDs
    const validNodeIds = new Set(rawNodes.map((n: any) => n.id));
    rawEdges = rawEdges.filter((e: any) => validNodeIds.has(e.source) && validNodeIds.has(e.target));

    // Highlighting connected nodes/edges if a node is selected
    const selectedId = selectedNode?.id;
    let connectedNodeIds = new Set<string>();
    let connectedEdgeIds = new Set<string>();

    if (selectedId) {
      connectedNodeIds.add(selectedId);
      rawEdges.forEach((edge) => {
        if (edge.source === selectedId || edge.target === selectedId) {
          connectedEdgeIds.add(edge.id);
          connectedNodeIds.add(edge.source);
          connectedNodeIds.add(edge.target);
        }
      });
    }

    const styledNodes = rawNodes.map((n) => {
      const isSelected = n.id === selectedId;
      const isHighlighted = connectedNodeIds.has(n.id);
      const isDimmed = selectedId ? !isHighlighted : false;
      return {
        ...n,
        selected: isSelected,
        data: {
          ...n.data,
          isHighlighted,
          isDimmed,
        },
      };
    });

    const styledEdges = rawEdges.map((e) => {
      const isConnected = connectedEdgeIds.has(e.id);
      const isDimmed = selectedId ? !isConnected : false;
      return {
        ...e,
        animated: enableFlowAnimation,
        style: {
          stroke: isConnected ? '#38bdf8' : isDarkMode ? '#475569' : '#94a3b8',
          strokeWidth: isConnected ? 3 : 2,
          opacity: isDimmed ? 0.25 : 1,
        },
      };
    });

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(styledNodes, styledEdges, layoutMode);
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [topoData, driverFilter, searchTerm, layoutMode, enableFlowAnimation, isDarkMode, selectedNode, setNodes, setEdges]);

  useEffect(() => {
    processAndLayoutGraph();
  }, [processAndLayoutGraph]);

  const handleNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNode({
      id: node.id,
      type: node.type || 'node',
      data: node.data as any,
    });
  };

  const handleClearHighlight = () => {
    setSelectedNode(null);
  };

  if (isLoading) return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading Multi-Host Topology Canvas...</div>;
  if (error) return <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>Error rendering multi-host topology canvas.</div>;

  return (
    <div
      style={{
        position: 'relative',
        background: isDarkMode ? '#0f172a' : '#ffffff',
        color: isDarkMode ? '#f8fafc' : '#0f172a',
        borderRadius: '12px',
        border: isDarkMode ? '1px solid #1e293b' : '1px solid #cbd5e1',
        overflow: 'hidden',
        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
        marginBottom: '2rem',
        transition: 'all 0.3s ease',
      }}
    >
      {/* Control Bar */}
      <div
        style={{
          padding: '0.85rem 1.25rem',
          background: isDarkMode ? '#1e293b' : '#f8fafc',
          borderBottom: isDarkMode ? '1px solid #334155' : '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: isDarkMode ? '#38bdf8' : '#0f172a' }}>
            🗺️ Multi-Host Fleet Topology
          </h3>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
            <span>Hosts: <strong>{topoData?.stats?.hosts_count || 0}</strong></span>
            <span>Networks: <strong>{topoData?.stats?.networks_count || 0}</strong></span>
            <span>Workloads: <strong>{topoData?.stats?.containers_count || 0}</strong></span>
          </div>
        </div>

        {/* Filters & Canvas Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="🔍 Search node..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              background: isDarkMode ? '#0f172a' : '#ffffff',
              color: isDarkMode ? '#f8fafc' : '#0f172a',
              fontSize: '0.85rem',
            }}
          />

          <select
            value={layoutMode}
            onChange={(e) => setLayoutMode(e.target.value as any)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              background: isDarkMode ? '#0f172a' : '#ffffff',
              color: isDarkMode ? '#38bdf8' : '#0284c7',
              fontSize: '0.85rem',
              fontWeight: 600,
            }}
          >
            <option value="tiered-3col">🏢 3-Column Fleet Layout (Host ➔ Net ➔ Container)</option>
            <option value="dagre-LR">↔️ Horizontal Pipeline Layout</option>
            <option value="dagre-TB">📐 Vertical Tier Layout</option>
            <option value="grid">🔳 Concentric Grid Layout</option>
          </select>

          <select
            value={envFilter}
            onChange={(e) => setEnvFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              background: isDarkMode ? '#0f172a' : '#ffffff',
              color: isDarkMode ? '#f8fafc' : '#0f172a',
              fontSize: '0.85rem',
              fontWeight: 600,
            }}
          >
            <option value="ALL">All Environments</option>
            <option value="production">Production</option>
            <option value="staging">Staging</option>
            <option value="development">Development</option>
            <option value="edge">Edge Fleet</option>
          </select>

          <select
            value={hostFilter}
            onChange={(e) => setHostFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              background: isDarkMode ? '#0f172a' : '#ffffff',
              color: isDarkMode ? '#f8fafc' : '#0f172a',
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Fleet Hosts</option>
            {(hostsList || []).map((h: any) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.id})
              </option>
            ))}
          </select>

          <select
            value={driverFilter}
            onChange={(e) => setDriverFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              background: isDarkMode ? '#0f172a' : '#ffffff',
              color: isDarkMode ? '#f8fafc' : '#0f172a',
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Drivers</option>
            <option value="bridge">bridge (Docker/Podman)</option>
            <option value="overlay">overlay (Swarm/Docker)</option>
            <option value="macvlan">macvlan</option>
            <option value="aws-vpc">aws-vpc (AWS Cloud)</option>
            <option value="azure-vnet">azure-vnet (Azure Cloud)</option>
            <option value="gcp-vpc">gcp-vpc (GCP Cloud)</option>
            <option value="vsphere-vds">vsphere-vds (VMware)</option>
            <option value="nutanix-ahv">nutanix-ahv (Nutanix AHV)</option>
            <option value="hyperv-vswitch">hyperv-vswitch (Hyper-V)</option>
            <option value="ovn-kubernetes">ovn-kubernetes (OpenShift/K8s)</option>
          </select>

          {/* Flow Animation Checkbox */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', cursor: 'pointer', color: isDarkMode ? '#cbd5e1' : '#475569' }}>
            <input
              type="checkbox"
              checked={enableFlowAnimation}
              onChange={(e) => setEnableFlowAnimation(e.target.checked)}
            />
            ⚡ Flow Animations
          </label>

          {/* Dark Mode Toggle */}
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{
              background: isDarkMode ? '#334155' : '#e2e8f0',
              border: 'none',
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 600,
              color: isDarkMode ? '#f8fafc' : '#0f172a',
            }}
          >
            {isDarkMode ? '☀️ Light' : '🌙 Dark Slate'}
          </button>

          <button
            onClick={() => refetch()}
            style={{
              background: isDarkMode ? '#334155' : '#f1f5f9',
              border: isDarkMode ? '1px solid #475569' : '1px solid #cbd5e1',
              color: isDarkMode ? '#f8fafc' : '#0f172a',
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            🔄 Refresh
          </button>

          <button
            onClick={() => setIsConnectModalOpen(true)}
            style={{
              background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
              border: 'none',
              color: '#ffffff',
              padding: '0.4rem 0.85rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              boxShadow: '0 2px 4px rgba(2, 132, 199, 0.3)',
            }}
          >
            🖥️ + Connect Host
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div style={{ height: '560px', width: '100%', background: isDarkMode ? '#0b0f19' : '#f8fafc', position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes as any}
          onNodeClick={handleNodeClick}
          fitView
        >
          <AutoFitView filterKey={`${envFilter}-${hostFilter}-${driverFilter}-${searchTerm}-${layoutMode}-${nodes.length}`} />
          <Background color={isDarkMode ? '#1e293b' : '#cbd5e1'} gap={16} size={1} />
          <Controls style={{ background: isDarkMode ? '#1e293b' : '#ffffff', borderRadius: '8px', border: isDarkMode ? '1px solid #334155' : '1px solid #cbd5e1' }} />
          <style>{`
            .react-flow__controls-button {
              background: ${isDarkMode ? '#1e293b' : '#ffffff'} !important;
              border-bottom: ${isDarkMode ? '1px solid #334155' : '1px solid #e2e8f0'} !important;
              fill: ${isDarkMode ? '#38bdf8' : '#0f172a'} !important;
              stroke: ${isDarkMode ? '#38bdf8' : '#0f172a'} !important;
              color: ${isDarkMode ? '#38bdf8' : '#0f172a'} !important;
            }
            .react-flow__controls-button:hover {
              background: ${isDarkMode ? '#334155' : '#f1f5f9'} !important;
            }
            .react-flow__controls-button svg {
              fill: ${isDarkMode ? '#38bdf8' : '#0f172a'} !important;
              stroke: ${isDarkMode ? '#38bdf8' : '#0f172a'} !important;
            }
          `}</style>
          <MiniMap style={{ background: isDarkMode ? '#1e293b' : '#f1f5f9' }} zoomable pannable />
        </ReactFlow>

        {/* Selected Path Reset Action Overlay */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              bottom: '1rem',
              left: '50%',
              transform: 'translateX(-50%)',
              background: '#0f172a',
              color: '#ffffff',
              padding: '0.5rem 1.25rem',
              borderRadius: '9999px',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              boxShadow: '0 10px 15px -3px rgba(0,0,0,0.4)',
              border: '1px solid #38bdf8',
              zIndex: 10,
            }}
          >
            <span>Focused on Node: <strong>{selectedNode.data.label}</strong></span>
            <button
              onClick={handleClearHighlight}
              style={{
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                padding: '0.25rem 0.75rem',
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
            >
              Reset Focus
            </button>
          </div>
        )}

        {/* Right-Hand Inspector Drawer */}
        <TopologyInspectorDrawer
          selectedNode={selectedNode}
          onClose={() => setSelectedNode(null)}
          onClearHighlight={handleClearHighlight}
        />

        {/* Connect Host Modal */}
        <ConnectHostModal
          isOpen={isConnectModalOpen}
          onClose={() => setIsConnectModalOpen(false)}
          onHostConnected={() => refetch()}
        />
      </div>
    </div>
  );
};

