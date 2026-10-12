import React from 'react';

export interface SelectedNodeDetails {
  id: string;
  type: 'containerNode' | 'networkNode' | 'hostNode' | 'hostGroupNode' | string;
  data: {
    label: string;
    sublabel?: string;
    status?: string;
    ip_address?: string;
    driver?: string;
    scope?: string;
    subnets?: Array<{ subnet: string; gateway?: string }>;
    environment?: string;
    host_id?: string;
    allocated_ips?: number;
    total_ips?: number;
    containers_count?: number;
    raw?: any;
  };
}

interface TopologyInspectorDrawerProps {
  selectedNode: SelectedNodeDetails | null;
  onClose: () => void;
  onClearHighlight: () => void;
}

export const TopologyInspectorDrawer: React.FC<TopologyInspectorDrawerProps> = ({
  selectedNode,
  onClose,
  onClearHighlight,
}) => {
  if (!selectedNode) return null;

  const { id, type, data } = selectedNode;

  const renderBadge = (label: string, color: string, bg: string) => (
    <span
      style={{
        display: 'inline-block',
        padding: '0.2rem 0.6rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        color,
        background: bg,
        marginRight: '0.5rem',
      }}
    >
      {label}
    </span>
  );

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '360px',
        height: '100%',
        background: '#0f172a',
        color: '#f8fafc',
        borderLeft: '1px solid #1e293b',
        boxShadow: '-10px 0 25px -5px rgba(0, 0, 0, 0.4)',
        zIndex: 20,
        display: 'flex',
        flexDirection: 'column',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#1e293b',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.2rem' }}>
            {type === 'containerNode' ? '📦' : type === 'networkNode' ? '🌐' : '🖥️'}
          </span>
          <div>
            <h4 style={{ margin: 0, fontSize: '1.05rem', color: '#38bdf8', fontWeight: 700 }}>
              {data.label}
            </h4>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
              ID: {id}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            fontSize: '1.25rem',
            cursor: 'pointer',
            padding: '0.25rem 0.5rem',
            borderRadius: '4px',
          }}
          title="Close Inspector"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
        {/* Node Type Indicator */}
        <div style={{ marginBottom: '1.25rem' }}>
          {type === 'containerNode' && renderBadge('Container Workload', '#22c55e', 'rgba(34, 197, 94, 0.15)')}
          {type === 'networkNode' && renderBadge('Virtual Network', '#38bdf8', 'rgba(56, 189, 248, 0.15)')}
          {(type === 'hostNode' || type === 'hostGroupNode') && renderBadge('Infrastructure Host', '#a855f7', 'rgba(168, 85, 247, 0.15)')}
          {data.environment && renderBadge(data.environment.toUpperCase(), '#eab308', 'rgba(234, 179, 8, 0.15)')}
        </div>

        {/* Detailed Specs List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Status */}
          {data.status && (
            <div style={{ background: '#1e293b', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Health Status</div>
              <div style={{ fontWeight: 600, color: data.status === 'running' || data.status === 'ONLINE' || data.status === 'HEALTHY' ? '#4ade80' : '#f87171' }}>
                ● {data.status.toUpperCase()}
              </div>
            </div>
          )}

          {/* IP Address */}
          {data.ip_address && (
            <div style={{ background: '#1e293b', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Assigned IPv4 Address</div>
              <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8', fontSize: '0.95rem' }}>
                {data.ip_address}
              </div>
            </div>
          )}

          {/* Subnets / CIDR */}
          {data.subnets && data.subnets.length > 0 && (
            <div style={{ background: '#1e293b', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Network Subnets (CIDR)</div>
              {data.subnets.map((sub: { subnet: string; gateway?: string }, idx: number) => (
                <div key={idx} style={{ marginTop: idx > 0 ? '0.5rem' : 0 }}>
                  <div style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8' }}>{sub.subnet}</div>
                  {sub.gateway && (
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>Gateway: {sub.gateway}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Driver & Scope */}
          {(data.driver || data.scope) && (
            <div style={{ background: '#1e293b', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Network Driver</div>
                <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{data.driver || 'N/A'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Scope</div>
                <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{data.scope || 'local'}</div>
              </div>
            </div>
          )}

          {/* Host ID / Location */}
          {data.host_id && (
            <div style={{ background: '#1e293b', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Parent Host</div>
              <div style={{ fontFamily: 'monospace', color: '#cbd5e1', fontSize: '0.85rem' }}>{data.host_id}</div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div style={{ padding: '1.25rem 1.5rem', borderTop: '1px solid #1e293b', background: '#1e293b', display: 'flex', gap: '0.75rem' }}>
        <button
          onClick={onClearHighlight}
          style={{
            flex: 1,
            background: '#334155',
            color: '#f8fafc',
            border: 'none',
            padding: '0.6rem 1rem',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          Reset Path Highlight
        </button>
      </div>
    </div>
  );
};
