import React, { useState, useEffect } from 'react';

interface ContainerOption {
  id: string;
  name: string;
  status: string;
}

interface ContainerAttachModalProps {
  networkId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ContainerAttachModal: React.FC<ContainerAttachModalProps> = ({ networkId, isOpen, onClose, onSuccess }) => {
  const [containers, setContainers] = useState<ContainerOption[]>([]);
  const [selectedContainerId, setSelectedContainerId] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [aliasInput, setAliasInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      setError(null);
      fetch('/api/v1/containers')
        .then((res) => res.json())
        .then((data) => {
          setContainers(data);
          if (data.length > 0) setSelectedContainerId(data[0].id);
        })
        .catch(() => setError('Failed to load container list'))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedContainerId) return;
    setIsSubmitting(true);
    setError(null);

    const aliases = aliasInput.split(',').map((a) => a.trim()).filter(Boolean);
    const payload = {
      container_id: selectedContainerId,
      ip_address: ipAddress || undefined,
      aliases,
    };

    try {
      const res = await fetch(`/api/v1/networks/${networkId}/containers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to attach container');
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#ffffff', borderRadius: '8px', padding: '1.5rem', width: '460px', maxWidth: '90%', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#0f172a' }}>Attach Workload Container</h3>
        {error && <div style={{ background: '#fef2f2', color: '#dc2626', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>Select Workload Container *</label>
            {isLoading ? (
              <div style={{ padding: '0.5rem', color: '#64748b', fontSize: '0.85rem' }}>Loading containers...</div>
            ) : containers.length > 0 ? (
              <select
                value={selectedContainerId}
                onChange={(e) => setSelectedContainerId(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e1' }}
              >
                {containers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.status})
                  </option>
                ))}
              </select>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No workload containers registered.</div>
            )}
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>Static IP Address (Optional)</label>
            <input
              type="text"
              value={ipAddress}
              onChange={(e) => setIpAddress(e.target.value)}
              placeholder="e.g. 172.17.0.100"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>Network DNS Aliases (Comma separated)</label>
            <input
              type="text"
              value={aliasInput}
              onChange={(e) => setAliasInput(e.target.value)}
              placeholder="api-service, backend-db"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || containers.length === 0}
              style={{ background: '#2563eb', color: '#ffffff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
            >
              {isSubmitting ? 'Attaching...' : 'Attach Endpoint'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
