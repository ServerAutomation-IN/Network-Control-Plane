import React, { useState } from 'react';
import { GitOpsManagement } from './GitOpsManagement';

export interface DriftDiffItem {
  resource_type: string;
  resource_name: string;
  host_id: string;
  drift_type: 'MISSING_IN_RUNTIME' | 'EXTRA_IN_RUNTIME' | 'MODIFIED_CONFIG';
  property_name?: string;
  desired_value?: any;
  actual_value?: any;
  severity: string;
  details?: string;
}

export interface ReconciliationAction {
  id: string;
  action_type: string;
  target_resource: string;
  host_id: string;
  parameters: Record<string, any>;
  risk_level: string;
  reason: string;
}

export interface ReconciliationJob {
  id: string;
  manifest_name: string;
  desired_yaml: string;
  drifts: DriftDiffItem[];
  plan_actions: ReconciliationAction[];
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'EXECUTED' | 'REJECTED';
  approved_by?: string;
  execution_result?: Record<string, any>;
  created_at: string;
  executed_at?: string;
}

const SAMPLE_MANIFEST_DEFAULT = `apiVersion: network-control-plane/v1
kind: NetworkManifest
metadata:
  name: production-fleet-manifest
  environment: production
spec:
  networks:
    - name: control_plane_frontend
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      subnets:
        - subnet: 172.19.0.0/16
          gateway: 172.19.0.1
    - name: control_plane_backend
      host_id: host-local-docker-host
      driver: bridge
      internal: false
      subnets:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
    - name: prod_payment_gateway_net
      host_id: host-docker-node-10.0.0.15
      driver: bridge
      internal: true
      subnets:
        - subnet: 172.35.0.0/16
          gateway: 172.35.0.1
`;

export const DriftDashboard: React.FC = () => {
  const [subTab, setSubTab] = useState<'editor' | 'gitops'>('editor');
  const [yamlContent, setYamlContent] = useState<string>(SAMPLE_MANIFEST_DEFAULT);
  const [activeJob, setActiveJob] = useState<ReconciliationJob | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<'admin' | 'operator' | 'viewer'>('admin');
  const [repoUrl, setRepoUrl] = useState<string>('https://github.com/org/network-manifests');

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': userRole,
    'X-User-Id': `user-${userRole}`,
  });

  const handleCompareDrift = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/drift/compare', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ desired_yaml: yamlContent }),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to compare desired state');
      }

      const data = await res.json();
      setActiveJob(data);
    } catch (err: any) {
      setError(err.message || 'Error comparing state');
    } finally {
      setLoading(false);
    }
  };

  const handleGitSync = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/drift/git-sync?repo_url=${encodeURIComponent(repoUrl)}`, {
        method: 'POST',
        headers: getHeaders(),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Git sync failed');
      }

      const data = await res.json();
      setYamlContent(data.desired_yaml);
      setActiveJob(data);
    } catch (err: any) {
      setError(err.message || 'Git sync error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovePlan = async () => {
    if (!activeJob) return;
    try {
      const res = await fetch(`/api/v1/drift/plans/${activeJob.id}/approve`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Approval failed');
      }
      const data = await res.json();
      setActiveJob(data);
    } catch (err: any) {
      alert(`Approval Error: ${err.message}`);
    }
  };

  const handleExecutePlan = async () => {
    if (!activeJob) return;
    if (!window.confirm('Execute approved reconciliation plan? This will mutate actual network infrastructure.')) return;

    try {
      const res = await fetch(`/api/v1/drift/plans/${activeJob.id}/execute`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Plan execution failed');
      }
      const data = await res.json();
      setActiveJob(data);
    } catch (err: any) {
      alert(`Execution Error: ${err.message}`);
    }
  };

  const getDriftBadge = (type: string) => {
    switch (type) {
      case 'MISSING_IN_RUNTIME':
        return { label: 'MISSING IN RUNTIME', bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' };
      case 'EXTRA_IN_RUNTIME':
        return { label: 'UNMANAGED DRIFT', bg: '#fef3c7', text: '#92400e', border: '#fcd34d' };
      default:
        return { label: 'MODIFIED CONFIG', bg: '#ffedd5', text: '#9a3412', border: '#fdba74' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Sub-Tab Switcher */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 700, color: '#0f172a' }}>
            🔄 Desired-State, Drift Detection & GitOps Dashboard
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Compare actual runtime infrastructure against declarative YAML specs and manage automated GitOps repositories.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.3rem', borderRadius: '8px' }}>
          <button
            onClick={() => setSubTab('editor')}
            style={{
              background: subTab === 'editor' ? '#0284c7' : 'transparent',
              color: subTab === 'editor' ? '#ffffff' : '#475569',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            📝 Declarative Spec & Plan
          </button>
          <button
            onClick={() => setSubTab('gitops')}
            style={{
              background: subTab === 'gitops' ? '#0284c7' : 'transparent',
              color: subTab === 'gitops' ? '#ffffff' : '#475569',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            🔄 GitOps Auto-Sync Repositories
          </button>
        </div>
      </div>

      {subTab === 'gitops' ? (
        <GitOpsManagement />
      ) : (
        <>
          {error && (
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b', padding: '1rem', borderRadius: '8px' }}>
              {error}
            </div>
          )}

          {/* Controls Bar */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: '#ffffff',
                padding: '0.4rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
              }}
            >
              <span style={{ fontWeight: 600, color: '#475569' }}>RBAC Role:</span>
              <select
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as any)}
                style={{ border: 'none', background: 'transparent', fontWeight: 700, color: '#2563eb', cursor: 'pointer' }}
              >
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>

            <button
              onClick={handleCompareDrift}
              disabled={loading}
              style={{
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.6rem 1.2rem',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              {loading ? 'Calculating Drift...' : '⚡ Compare Desired vs Actual'}
            </button>
          </div>

          {/* Editor & Action Plan Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
            {/* Declarative Spec Editor */}
            <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                  📝 Declarative Desired-State Manifest (YAML)
                </h3>
                <span style={{ fontSize: '0.75rem', color: '#0284c7', background: '#e0f2fe', padding: '0.2rem 0.5rem', borderRadius: '6px', fontWeight: 600 }}>
                  apiVersion: network-control-plane/v1
                </span>
              </div>

              <textarea
                value={yamlContent}
                onChange={(e) => setYamlContent(e.target.value)}
                rows={14}
                style={{
                  fontFamily: 'Consolas, Monaco, monospace',
                  fontSize: '0.85rem',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#0f172a',
                  color: '#f8fafc',
                  resize: 'vertical',
                  lineHeight: '1.4',
                }}
              />

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="Git Repository URL"
                  style={{ flex: 1, padding: '0.5rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <button
                  onClick={handleGitSync}
                  disabled={loading}
                  style={{ background: '#4f46e5', color: '#ffffff', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
                >
                  🔄 Git Sync
                </button>
              </div>
            </div>

            {/* Active Reconciliation Plan & Approval Gate */}
            <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                  🎯 Reconciliation Plan & Approval Gate
                </h3>
                {activeJob && (
                  <span
                    style={{
                      background: activeJob.status === 'APPROVED' ? '#dcfce7' : activeJob.status === 'EXECUTED' ? '#e0e7ff' : '#fef3c7',
                      color: activeJob.status === 'APPROVED' ? '#166534' : activeJob.status === 'EXECUTED' ? '#3730a3' : '#92400e',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                    }}
                  >
                    {activeJob.status}
                  </span>
                )}
              </div>

              {!activeJob ? (
                <div style={{ padding: '3rem 1rem', textAlign: 'center', color: '#64748b', fontSize: '0.9rem' }}>
                  Click <strong>⚡ Compare Desired vs Actual</strong> above to calculate infrastructure drift and generate a human-in-the-loop approval plan.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.85rem' }}>
                    <div><strong>Manifest:</strong> {activeJob.manifest_name}</div>
                    <div><strong>Drift Diffs Count:</strong> {activeJob.drifts.length}</div>
                    <div><strong>Reconciliation Actions:</strong> {activeJob.plan_actions.length}</div>
                    {activeJob.approved_by && <div><strong>Approved By:</strong> {activeJob.approved_by}</div>}
                  </div>

                  {/* Action items list */}
                  <div style={{ maxHeight: '220px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {activeJob.plan_actions.map((act) => (
                      <div
                        key={act.id}
                        style={{
                          padding: '0.6rem 0.8rem',
                          borderRadius: '6px',
                          border: '1px solid #e2e8f0',
                          background: act.action_type === 'CREATE_NETWORK' ? '#f0fdf4' : '#fff1f2',
                          fontSize: '0.85rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <strong style={{ color: act.action_type === 'CREATE_NETWORK' ? '#166534' : '#9f1239' }}>
                            [{act.action_type}] {act.target_resource}
                          </strong>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{act.reason}</div>
                        </div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: act.risk_level === 'HIGH' ? '#dc2626' : '#16a34a' }}>
                          Risk: {act.risk_level}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Approval & Execution Buttons */}
                  <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                    {activeJob.status === 'PENDING_APPROVAL' && (
                      <button
                        onClick={handleApprovePlan}
                        disabled={userRole === 'viewer'}
                        style={{
                          flex: 1,
                          background: '#16a34a',
                          color: '#ffffff',
                          border: 'none',
                          padding: '0.65rem',
                          borderRadius: '6px',
                          fontWeight: 700,
                          cursor: userRole === 'viewer' ? 'not-allowed' : 'pointer',
                        }}
                      >
                        👍 Approve Reconciliation Plan
                      </button>
                    )}

                    {activeJob.status === 'APPROVED' && (
                      <button
                        onClick={handleExecutePlan}
                        disabled={userRole === 'viewer'}
                        style={{
                          flex: 1,
                          background: '#d97706',
                          color: '#ffffff',
                          border: 'none',
                          padding: '0.65rem',
                          borderRadius: '6px',
                          fontWeight: 700,
                          cursor: userRole === 'viewer' ? 'not-allowed' : 'pointer',
                        }}
                      >
                        🚀 Execute Approved Actions
                      </button>
                    )}

                    {activeJob.status === 'EXECUTED' && (
                      <div style={{ padding: '0.6rem', textAlign: 'center', width: '100%', background: '#f0fdf4', color: '#166534', borderRadius: '6px', fontWeight: 700, fontSize: '0.875rem' }}>
                        ✅ Plan Successfully Executed & Reconciled!
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Discovered Drift Diffs Table */}
          {activeJob && (
            <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
              <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontWeight: 700, fontSize: '1rem', color: '#0f172a' }}>
                Infrastructure Drift Diffs ({activeJob.drifts.length})
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Resource</th>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Host Node</th>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Drift Type</th>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Desired Spec</th>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Actual Runtime</th>
                      <th style={{ padding: '0.75rem 1.25rem' }}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeJob.drifts.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#16a34a', fontWeight: 600 }}>
                          🎉 Zero Drift Detected! Runtime infrastructure matches desired YAML specification perfectly.
                        </td>
                      </tr>
                    ) : (
                      activeJob.drifts.map((d, idx) => {
                        const badge = getDriftBadge(d.drift_type);
                        return (
                          <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                            <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: '#0f172a' }}>{d.resource_name}</td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#64748b' }}><code>{d.host_id}</code></td>
                            <td style={{ padding: '0.85rem 1.25rem' }}>
                              <span
                                style={{
                                  background: badge.bg,
                                  color: badge.text,
                                  border: `1px solid ${badge.border}`,
                                  padding: '0.2rem 0.5rem',
                                  borderRadius: '8px',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                }}
                              >
                                {badge.label}
                              </span>
                            </td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#166534', fontFamily: 'monospace' }}>
                              {String(d.desired_value ?? 'N/A')}
                            </td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#991b1b', fontFamily: 'monospace' }}>
                              {String(d.actual_value ?? 'N/A')}
                            </td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#475569' }}>{d.details}</td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
