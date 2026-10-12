import React, { useState, useEffect } from 'react';

interface SafetyAssessment {
  network_id: string;
  network_name: string;
  risk_level: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  attached_containers_count: number;
  impacted_containers: Array<{ container_id: string; name: string; status: string; ip_address?: string }>;
  compose_project?: string;
  is_safe_to_delete: boolean;
  risk_factors: string[];
}

interface NetworkDeleteModalProps {
  networkId: string | null;
  networkName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const NetworkDeleteModal: React.FC<NetworkDeleteModalProps> = ({ networkId, networkName, isOpen, onClose, onSuccess }) => {
  const [assessment, setAssessment] = useState<SafetyAssessment | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [force, setForce] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && networkId) {
      setIsLoading(true);
      setError(null);
      fetch(`/api/v1/networks/${networkId}/safety-check`)
        .then((res) => res.json())
        .then((data) => setAssessment(data))
        .catch((err) => setError('Failed to fetch safety assessment'))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, networkId]);

  if (!isOpen || !networkId) return null;

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/networks/${networkId}?force=${force}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to delete network');
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error deleting network');
    } finally {
      setIsDeleting(false);
    }
  };

  const getBadgeStyle = (level?: string) => {
    switch (level) {
      case 'CRITICAL': return { bg: '#fee2e2', color: '#991b1b' };
      case 'HIGH': return { bg: '#ffedd5', color: '#c2410c' };
      case 'MEDIUM': return { bg: '#fef9c3', color: '#a16207' };
      case 'LOW':
      default: return { bg: '#dcfce7', color: '#15803d' };
    }
  };

  const badgeStyle = getBadgeStyle(assessment?.risk_level);

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#ffffff', borderRadius: '8px', padding: '1.5rem', width: '520px', maxWidth: '90%', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#0f172a' }}>Pre-Deletion Safety Verification</h3>
        <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
          Evaluating risk analysis for deleting network <strong>{networkName}</strong>.
        </p>

        {isLoading ? (
          <div style={{ padding: '2rem 0', textAlign: 'center', color: '#64748b' }}>Calculating safety assessment...</div>
        ) : assessment ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', background: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.9rem', color: '#475569', fontWeight: 600 }}>Risk Assessment Rating:</span>
              <span style={{ background: badgeStyle.bg, color: badgeStyle.color, padding: '0.25rem 0.6rem', borderRadius: '4px', fontWeight: 700, fontSize: '0.85rem' }}>
                {assessment.risk_level} RISK
              </span>
            </div>

            {assessment.risk_factors.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#dc2626', marginBottom: '0.4rem' }}>Risk Factors Detected:</div>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#991b1b', fontSize: '0.85rem' }}>
                  {assessment.risk_factors.map((rf, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>{rf}</li>
                  ))}
                </ul>
              </div>
            )}

            {assessment.impacted_containers.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.4rem' }}>Impacted Container Workloads ({assessment.impacted_containers.length}):</div>
                <div style={{ maxHeight: '120px', overflowY: 'auto', background: '#f1f5f9', padding: '0.5rem', borderRadius: '4px', fontSize: '0.8rem' }}>
                  {assessment.impacted_containers.map((c) => (
                    <div key={c.container_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0' }}>
                      <span><strong>{c.name}</strong> ({c.status})</span>
                      <span style={{ color: '#64748b' }}>{c.ip_address || 'No IP'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!assessment.is_safe_to_delete && (
              <div style={{ marginBottom: '1rem', background: '#fff7ed', border: '1px solid #ffedd5', padding: '0.75rem', borderRadius: '4px' }}>
                <label style={{ fontSize: '0.85rem', color: '#c2410c', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
                  Force delete network despite active risk factors
                </label>
              </div>
            )}
          </div>
        ) : null}

        {error && <div style={{ background: '#fef2f2', color: '#dc2626', padding: '0.75rem', borderRadius: '4px', margin: '1rem 0 0 0', fontSize: '0.85rem' }}>{error}</div>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting || (!assessment?.is_safe_to_delete && !force)}
            style={{
              background: assessment?.is_safe_to_delete || force ? '#dc2626' : '#94a3b8',
              color: '#ffffff',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: assessment?.is_safe_to_delete || force ? 'pointer' : 'not-allowed',
              fontWeight: 600,
            }}
          >
            {isDeleting ? 'Deleting...' : 'Confirm Deletion'}
          </button>
        </div>
      </div>
    </div>
  );
};
