import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { NetworkItem } from './NetworkList';
import { ContainerAttachModal } from './ContainerAttachModal';

interface ContainerAttachment {
  id: string;
  name: string;
  image: string;
  status: string;
  attachments?: Array<{
    network_id: string;
    ip_address?: string;
    mac_address?: string;
    aliases?: string[];
  }>;
  network_attachments?: Array<{
    network_id: string;
    ip_address?: string;
    mac_address?: string;
    aliases?: string[];
  }>;
}

const fetchNetworkDetail = async (networkId: string): Promise<NetworkItem> => {
  const res = await fetch(`/api/v1/networks/${networkId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch network detail');
  }
  return res.json();
};

const fetchContainers = async (): Promise<ContainerAttachment[]> => {
  const res = await fetch('/api/v1/containers');
  if (!res.ok) return [];
  return res.json();
};

export const NetworkDetail: React.FC<{ networkId: string; onBack: () => void }> = ({ networkId, onBack }) => {
  const { role } = useAuth();
  const isViewer = role === 'viewer';
  const [isAttachOpen, setIsAttachOpen] = useState(false);
  const [detachError, setDetachError] = useState<string | null>(null);

  const { data: network, isLoading: isNetLoading, error: netError, refetch: refetchNetwork } = useQuery<NetworkItem>({
    queryKey: ['network', networkId],
    queryFn: () => fetchNetworkDetail(networkId),
  });

  const { data: containers, refetch: refetchContainers } = useQuery<ContainerAttachment[]>({
    queryKey: ['containers'],
    queryFn: fetchContainers,
  });

  if (isNetLoading) return <div style={{ padding: '1rem', color: '#64748b' }}>Loading network details...</div>;
  if (netError || !network) return <div style={{ padding: '1rem', color: '#ef4444' }}>Error loading details.</div>;

  const getAttachments = (cnt: ContainerAttachment) => cnt.attachments || cnt.network_attachments || [];

  // Filter containers attached to this network
  const attachedContainers = containers
    ? containers.filter((cnt) => getAttachments(cnt).some((att) => att.network_id === networkId))
    : [];

  const handleDetach = async (containerId: string) => {
    setDetachError(null);
    try {
      const res = await fetch(`/api/v1/networks/${networkId}/containers/${containerId}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to detach container');
      }
      refetchNetwork();
      refetchContainers();
    } catch (err: any) {
      setDetachError(err.message || 'Error detaching container');
    }
  };

  const handleSuccessAttach = () => {
    refetchNetwork();
    refetchContainers();
  };

  return (
    <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.5rem' }}>
      <button
        onClick={onBack}
        style={{ marginBottom: '1rem', background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' }}
      >
        ← Back to Networks List
      </button>
      <h2 style={{ marginTop: 0, color: '#0f172a' }}>{network.name}</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Driver</div>
          <div style={{ fontWeight: 600, fontSize: '1.1rem', color: '#0369a1' }}>{network.driver}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Scope</div>
          <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{network.scope}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Internal</div>
          <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>{network.internal ? 'Yes' : 'No'}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Attached Workloads</div>
          <div style={{ fontWeight: 600, fontSize: '1.1rem', color: '#16a34a' }}>{attachedContainers.length}</div>
        </div>
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', color: '#0f172a' }}>Subnet Configuration</h3>
        {network.subnets && network.subnets.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#334155' }}>
            {network.subnets.map((sub, idx) => (
              <li key={idx} style={{ marginBottom: '0.25rem' }}>
                Subnet: <strong>{sub.subnet || 'N/A'}</strong> | Gateway: <strong>{sub.gateway || 'N/A'}</strong> | IP Range: <strong>{sub.ip_range || 'N/A'}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: '#64748b', margin: 0 }}>No subnets configured for this network.</p>
        )}
      </div>

      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>Attached Workload Containers ({attachedContainers.length})</h3>
          <button
            onClick={() => !isViewer && setIsAttachOpen(true)}
            disabled={isViewer}
            title={isViewer ? 'Viewer role is read-only. Operator or Admin role required.' : 'Attach Workload'}
            style={{
              background: isViewer ? '#94a3b8' : '#2563eb',
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
            + Attach Workload
          </button>
        </div>

        {detachError && (
          <div style={{ background: '#fef2f2', color: '#dc2626', padding: '0.5rem 0.75rem', borderRadius: '4px', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
            {detachError}
          </div>
        )}

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
              <th style={{ padding: '0.6rem 1rem' }}>Container Name</th>
              <th style={{ padding: '0.6rem 1rem' }}>Image</th>
              <th style={{ padding: '0.6rem 1rem' }}>IP Address</th>
              <th style={{ padding: '0.6rem 1rem' }}>Status</th>
              <th style={{ padding: '0.6rem 1rem' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {attachedContainers.length > 0 ? (
              attachedContainers.map((cnt) => {
                const att = getAttachments(cnt).find((a) => a.network_id === networkId);
                return (
                  <tr key={cnt.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.6rem 1rem', fontWeight: 600 }}>{cnt.name}</td>
                    <td style={{ padding: '0.6rem 1rem', color: '#64748b' }}>{cnt.image || 'N/A'}</td>
                    <td style={{ padding: '0.6rem 1rem', fontFamily: 'monospace', color: '#0284c7' }}>
                      {att?.ip_address || 'Dynamic IP'}
                    </td>
                    <td style={{ padding: '0.6rem 1rem' }}>
                      <span style={{ background: cnt.status === 'running' ? '#dcfce7' : '#f1f5f9', color: cnt.status === 'running' ? '#15803d' : '#64748b', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600 }}>
                        {cnt.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.6rem 1rem' }}>
                      <button
                        onClick={() => !isViewer && handleDetach(cnt.id)}
                        disabled={isViewer}
                        title={isViewer ? 'Viewer role is read-only. Operator or Admin role required.' : 'Detach Workload'}
                        style={{
                          background: isViewer ? '#cbd5e1' : '#ef4444',
                          color: isViewer ? '#64748b' : '#ffffff',
                          border: 'none',
                          padding: '0.3rem 0.6rem',
                          borderRadius: '4px',
                          cursor: isViewer ? 'not-allowed' : 'pointer',
                          fontSize: '0.8rem',
                          opacity: isViewer ? 0.6 : 1,
                        }}
                      >
                        Detach
                      </button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} style={{ padding: '1.25rem', textAlign: 'center', color: '#94a3b8' }}>
                  No container workloads currently attached to this network.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <ContainerAttachModal
        networkId={networkId}
        isOpen={isAttachOpen}
        onClose={() => setIsAttachOpen(false)}
        onSuccess={handleSuccessAttach}
      />
    </div>
  );
};
