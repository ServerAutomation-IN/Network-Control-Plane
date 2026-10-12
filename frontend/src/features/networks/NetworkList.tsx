import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { NetworkCreateModal } from './NetworkCreateModal';
import { NetworkDeleteModal } from './NetworkDeleteModal';

export interface Subnet {
  subnet?: string;
  gateway?: string;
  ip_range?: string;
}

export interface NetworkItem {
  id: string;
  host_id?: string;
  host_name?: string;
  name: string;
  driver: string;
  scope: string;
  internal: boolean;
  attachable: boolean;
  container_count: number;
  subnets: Subnet[];
}

const fetchNetworks = async (): Promise<NetworkItem[]> => {
  const res = await fetch('/api/v1/networks');
  if (!res.ok) {
    throw new Error('Failed to fetch networks');
  }
  return res.json();
};

export const NetworkList: React.FC<{ onSelectNetwork: (id: string) => void }> = ({ onSelectNetwork }) => {
  const { role } = useAuth();
  const isViewer = role === 'viewer';

  const { data: networks, isLoading, error, refetch } = useQuery<NetworkItem[]>({
    queryKey: ['networks'],
    queryFn: fetchNetworks,
  });

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  if (isLoading) return <div style={{ padding: '1rem', color: '#64748b' }}>Loading networks...</div>;
  if (error) return <div style={{ padding: '1rem', color: '#ef4444' }}>Error loading networks.</div>;

  return (
    <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      <div style={{ padding: '1rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>Discovered Networks ({networks?.length || 0})</h3>
        <button
          onClick={() => !isViewer && setIsCreateOpen(true)}
          disabled={isViewer}
          title={isViewer ? 'Viewer role is read-only. Operator or Admin role required.' : 'Create Network'}
          style={{
            background: isViewer ? '#94a3b8' : '#16a34a',
            color: '#ffffff',
            border: 'none',
            padding: '0.4rem 0.8rem',
            borderRadius: '4px',
            cursor: isViewer ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            fontSize: '0.85rem',
            opacity: isViewer ? 0.7 : 1,
          }}
        >
          + Create Network
        </button>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
            <th style={{ padding: '0.75rem 1rem' }}>Name</th>
            <th style={{ padding: '0.75rem 1rem' }}>Host / Node</th>
            <th style={{ padding: '0.75rem 1rem' }}>Driver</th>
            <th style={{ padding: '0.75rem 1rem' }}>Scope</th>
            <th style={{ padding: '0.75rem 1rem' }}>Subnet / Gateway</th>
            <th style={{ padding: '0.75rem 1rem' }}>Workloads</th>
            <th style={{ padding: '0.75rem 1rem' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {networks && networks.length > 0 ? (
            networks.map((net) => (
              <tr key={net.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{net.name}</td>
                <td style={{ padding: '0.75rem 1rem' }}>
                  <span style={{ background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600 }}>
                    🖥️ {net.host_name || net.host_id || 'Local Host'}
                  </span>
                </td>
                <td style={{ padding: '0.75rem 1rem' }}>
                  <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem' }}>
                    {net.driver}
                  </span>
                </td>
                <td style={{ padding: '0.75rem 1rem', color: '#64748b' }}>{net.scope}</td>
                <td style={{ padding: '0.75rem 1rem' }}>
                  {net.subnets && net.subnets.length > 0
                    ? `${net.subnets[0].subnet || 'N/A'} (${net.subnets[0].gateway || 'No GW'})`
                    : 'N/A'}
                </td>
                <td style={{ padding: '0.75rem 1rem' }}>{net.container_count} containers</td>
                <td style={{ padding: '0.75rem 1rem', display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => onSelectNetwork(net.id)}
                    style={{ background: '#2563eb', color: '#ffffff', border: 'none', padding: '0.35rem 0.75rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}
                  >
                    Inspect
                  </button>
                  <button
                    onClick={() => !isViewer && setDeleteTarget({ id: net.id, name: net.name })}
                    disabled={isViewer}
                    title={isViewer ? 'Viewer role is read-only. Operator or Admin role required.' : 'Delete Network'}
                    style={{
                      background: isViewer ? '#cbd5e1' : '#ef4444',
                      color: isViewer ? '#64748b' : '#ffffff',
                      border: 'none',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '4px',
                      cursor: isViewer ? 'not-allowed' : 'pointer',
                      fontSize: '0.85rem',
                      opacity: isViewer ? 0.6 : 1,
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={7} style={{ padding: '1.5rem', textAlign: 'center', color: '#94a3b8' }}>
                No networks discovered yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <NetworkCreateModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={() => refetch()}
      />

      <NetworkDeleteModal
        networkId={deleteTarget?.id || null}
        networkName={deleteTarget?.name || ''}
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onSuccess={() => refetch()}
      />
    </div>
  );
};
