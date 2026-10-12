import React, { useEffect, useState } from 'react';

export interface PolicyRulesSpec {
  allowed_drivers?: string[];
  blocked_drivers?: string[];
  required_labels?: Record<string, string>;
  required_label_keys?: string[];
  approved_cidr_ranges?: string[];
  require_internal?: boolean;
  max_subnets_per_network?: number;
}

export interface NetworkPolicy {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  rules: PolicyRulesSpec;
  created_at: string;
  updated_at: string;
}

export interface ViolationDetail {
  rule_type: string;
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface PolicyResultResponse {
  id: string;
  policy_id: string;
  policy_name: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  network_id: string;
  network_name: string;
  host_id: string;
  status: 'COMPLIANT' | 'NON_COMPLIANT';
  violations: ViolationDetail[];
  evaluated_at: string;
}

export interface ComplianceReport {
  total_networks: number;
  compliant_count: number;
  non_compliant_count: number;
  compliance_percentage: number;
  violations_by_severity: Record<string, number>;
  results: PolicyResultResponse[];
}

export const PolicyDashboard: React.FC = () => {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [policies, setPolicies] = useState<NetworkPolicy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<'admin' | 'operator' | 'viewer'>('admin');
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Form state for creating a policy
  const [newPolicyName, setNewPolicyName] = useState<string>('');
  const [newPolicyDesc, setNewPolicyDesc] = useState<string>('');
  const [newPolicySeverity, setNewPolicySeverity] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('HIGH');
  const [allowedDriversStr, setAllowedDriversStr] = useState<string>('');
  const [blockedDriversStr, setBlockedDriversStr] = useState<string>('');
  const [approvedCidrsStr, setApprovedCidrsStr] = useState<string>('');

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': userRole,
    'X-User-Id': `user-${userRole}`,
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [policiesRes, complianceRes] = await Promise.all([
        fetch('/api/v1/policies', { headers: getHeaders() }),
        fetch('/api/v1/policies/compliance', { headers: getHeaders() }),
      ]);

      if (!policiesRes.ok || !complianceRes.ok) {
        throw new Error('Failed to fetch governance policies or compliance data.');
      }

      const policiesData = await policiesRes.json();
      const complianceData = await complianceRes.json();

      setPolicies(policiesData);
      setReport(complianceData);
    } catch (err: any) {
      setError(err.message || 'Error connecting to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [userRole]);

  const handleTriggerEvaluation = async () => {
    setEvaluating(true);
    try {
      const res = await fetch('/api/v1/policies/evaluate', {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Evaluation trigger failed.');
      }
      await fetchData();
    } catch (err: any) {
      alert(`Error triggering evaluation: ${err.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPolicyName.trim()) return;

    const allowed_drivers = allowedDriversStr
      ? allowedDriversStr.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined;

    const blocked_drivers = blockedDriversStr
      ? blockedDriversStr.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined;

    const approved_cidr_ranges = approvedCidrsStr
      ? approvedCidrsStr.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined;

    const payload = {
      name: newPolicyName,
      description: newPolicyDesc || undefined,
      enabled: true,
      severity: newPolicySeverity,
      rules: {
        allowed_drivers,
        blocked_drivers,
        approved_cidr_ranges,
      },
    };

    try {
      const res = await fetch('/api/v1/policies', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to create policy');
      }

      setShowCreateModal(false);
      setNewPolicyName('');
      setNewPolicyDesc('');
      setAllowedDriversStr('');
      setBlockedDriversStr('');
      setApprovedCidrsStr('');
      await fetchData();
    } catch (err: any) {
      alert(`Policy Creation Error: ${err.message}`);
    }
  };

  const handleDeletePolicy = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this governance policy?')) return;
    try {
      const res = await fetch(`/api/v1/policies/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to delete policy');
      }
      await fetchData();
    } catch (err: any) {
      alert(`Delete Error: ${err.message}`);
    }
  };

  const getSeverityBadgeColor = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' };
      case 'HIGH':
        return { bg: '#ffedd5', text: '#9a3412', border: '#fdba74' };
      case 'MEDIUM':
        return { bg: '#fef9c3', text: '#854d0e', border: '#fde047' };
      default:
        return { bg: '#e0f2fe', text: '#075985', border: '#7dd3fc' };
    }
  };

  if (loading && !report) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
        Loading Governance Policies & Compliance Data...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header & RBAC Role Switcher */}
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
            🛡️ Policy Governance & Compliance Dashboard
          </h2>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Enforce network drivers, label validation, CIDR boundaries, and RBAC security rules.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* RBAC Role Selector */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#f8fafc',
              padding: '0.4rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              fontSize: '0.85rem',
            }}
          >
            <span style={{ fontWeight: 600, color: '#475569' }}>Active Role (RBAC):</span>
            <select
              value={userRole}
              onChange={(e) => setUserRole(e.target.value as any)}
              style={{
                border: 'none',
                background: 'transparent',
                fontWeight: 700,
                color: userRole === 'admin' ? '#2563eb' : userRole === 'operator' ? '#d97706' : '#64748b',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="admin">Admin (Full Access)</option>
              <option value="operator">Operator (Mutate Ops)</option>
              <option value="viewer">Viewer (Read Only)</option>
            </select>
          </div>

          <button
            onClick={handleTriggerEvaluation}
            disabled={evaluating || userRole === 'viewer'}
            style={{
              background: userRole === 'viewer' ? '#94a3b8' : '#2563eb',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '0.6rem 1.2rem',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: userRole === 'viewer' ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            {evaluating ? 'Evaluating...' : '⚡ Evaluate All Policies'}
          </button>

          {userRole === 'admin' && (
            <button
              onClick={() => setShowCreateModal(true)}
              style={{
                background: '#059669',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.6rem 1.2rem',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              + Create Policy
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b', padding: '1rem', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      {/* Compliance Overview Summary Cards */}
      {report && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Total Networks Evaluated</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0f172a', marginTop: '0.4rem' }}>
              {report.total_networks}
            </div>
          </div>

          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Compliant Networks</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#16a34a', marginTop: '0.4rem' }}>
              {report.compliant_count}
            </div>
          </div>

          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Non-Compliant Networks</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: report.non_compliant_count > 0 ? '#dc2626' : '#16a34a', marginTop: '0.4rem' }}>
              {report.non_compliant_count}
            </div>
          </div>

          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Overall Compliance %</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: report.compliance_percentage >= 90 ? '#16a34a' : '#d97706', marginTop: '0.4rem' }}>
              {report.compliance_percentage}%
            </div>
          </div>
        </div>
      )}

      {/* Declarative Governance Policies Table */}
      <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontWeight: 700, fontSize: '1rem', color: '#0f172a' }}>
          Active Policy Definitions ({policies.length})
        </div>

        {policies.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            No declarative policies defined yet. Click <strong>+ Create Policy</strong> to define governance rules.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Policy Name</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Severity</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Rules Summary</th>
                  <th style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {policies.map((p) => {
                  const badge = getSeverityBadgeColor(p.severity);
                  return (
                    <tr key={p.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '1rem 1.25rem', fontWeight: 600, color: '#0f172a' }}>
                        {p.name}
                        {p.description && <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 400 }}>{p.description}</div>}
                      </td>
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <span
                          style={{
                            background: badge.bg,
                            color: badge.text,
                            border: `1px solid ${badge.border}`,
                            padding: '0.2rem 0.6rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                          }}
                        >
                          {p.severity}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <span style={{ color: p.enabled ? '#16a34a' : '#94a3b8', fontWeight: 600 }}>
                          {p.enabled ? '● Enabled' : '○ Disabled'}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1.25rem', fontSize: '0.85rem', color: '#334155' }}>
                        {p.rules.allowed_drivers && <div>Allowed Drivers: <code>{p.rules.allowed_drivers.join(', ')}</code></div>}
                        {p.rules.blocked_drivers && <div>Forbidden Drivers: <code>{p.rules.blocked_drivers.join(', ')}</code></div>}
                        {p.rules.approved_cidr_ranges && <div>Approved CIDRs: <code>{p.rules.approved_cidr_ranges.join(', ')}</code></div>}
                      </td>
                      <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                        {userRole === 'admin' ? (
                          <button
                            onClick={() => handleDeletePolicy(p.id)}
                            style={{ background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '6px', padding: '0.4rem 0.8rem', fontWeight: 600, cursor: 'pointer', fontSize: '0.8rem' }}
                          >
                            Delete
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Admin Only</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Non-Compliant Policy Violations Table */}
      {report && (
        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', background: '#fff1f2', fontWeight: 700, fontSize: '1rem', color: '#9f1239', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>⚠️ Compliance Violations ({report.results.filter(r => r.status === 'NON_COMPLIANT').length})</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', color: '#475569', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Network</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Host Node</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Policy Rule</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Violation Message</th>
                  <th style={{ padding: '0.75rem 1.25rem' }}>Severity</th>
                </tr>
              </thead>
              <tbody>
                {report.results.filter((r) => r.status === 'NON_COMPLIANT').length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: '#16a34a', fontWeight: 600 }}>
                      🎉 Zero Policy Violations! All networks are fully compliant with active governance specifications.
                    </td>
                  </tr>
                ) : (
                  report.results
                    .filter((r) => r.status === 'NON_COMPLIANT')
                    .map((res) =>
                      res.violations.map((v, idx) => {
                        const badge = getSeverityBadgeColor(v.severity);
                        return (
                          <tr key={`${res.id}-${idx}`} style={{ borderBottom: '1px solid #e2e8f0' }}>
                            <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: '#0f172a' }}>{res.network_name}</td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#64748b' }}><code>{res.host_id}</code></td>
                            <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: '#334155' }}>{res.policy_name}</td>
                            <td style={{ padding: '0.85rem 1.25rem', color: '#991b1b', fontWeight: 500 }}>{v.message}</td>
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
                                {v.severity}
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal for Creating Policy */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '12px',
              padding: '2rem',
              width: '100%',
              maxWidth: '520px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
          >
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
              Create Declarative Policy
            </h3>
            <form onSubmit={handleCreatePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Policy Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Production Driver & CIDR Boundary Policy"
                  value={newPolicyName}
                  onChange={(e) => setNewPolicyName(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Severity Level
                </label>
                <select
                  value={newPolicySeverity}
                  onChange={(e) => setNewPolicySeverity(e.target.value as any)}
                  style={{ width: '100%', padding: '0.6rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Allowed Drivers (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="bridge, overlay"
                  value={allowedDriversStr}
                  onChange={(e) => setAllowedDriversStr(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Forbidden Drivers (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="macvlan, host"
                  value={blockedDriversStr}
                  onChange={(e) => setBlockedDriversStr(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Approved CIDR Ranges (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="172.16.0.0/12, 10.0.0.0/8"
                  value={approvedCidrsStr}
                  onChange={(e) => setApprovedCidrsStr(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.9rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{ background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '6px', padding: '0.6rem 1.2rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ background: '#059669', color: '#ffffff', border: 'none', borderRadius: '6px', padding: '0.6rem 1.2rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  Save Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
