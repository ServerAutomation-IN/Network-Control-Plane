import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface SubnetDetail {
  network_id: string;
  network_name: string;
  host_id?: string;
  host_name?: string;
  driver: string;
  subnet: string;
  gateway?: string;
  total_ips: number;
  usable_ips: number;
  allocated_ips: number;
  utilization_percentage: number;
}

export interface IPAMConflict {
  conflict_type: string;
  severity: string;
  description: string;
  affected_network_ids: string[];
  details: Record<string, any>;
}

const fetchSubnets = async (): Promise<SubnetDetail[]> => {
  const res = await fetch('/api/v1/ipam/subnets');
  if (!res.ok) throw new Error('Failed to fetch IPAM subnets');
  return res.json();
};

const fetchConflicts = async (): Promise<IPAMConflict[]> => {
  const res = await fetch('/api/v1/ipam/conflicts');
  if (!res.ok) return [];
  return res.json();
};

export const IPAMDashboard: React.FC = () => {
  const { data: subnets, isLoading: isSubLoading, error: subError } = useQuery({
    queryKey: ['ipam_subnets'],
    queryFn: fetchSubnets,
    refetchInterval: 5000,
  });

  const { data: conflicts } = useQuery({
    queryKey: ['ipam_conflicts'],
    queryFn: fetchConflicts,
    refetchInterval: 5000,
  });

  const [valSubnet, setValSubnet] = useState('');
  const [valIp, setValIp] = useState('');
  const [valResult, setValResult] = useState<any | null>(null);

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valSubnet) return;
    try {
      const res = await fetch('/api/v1/ipam/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subnet: valSubnet, requested_ip: valIp || undefined }),
      });
      const data = await res.json();
      setValResult(data);
    } catch {
      setValResult({ is_valid: false, errors: ['Validation service unavailable'] });
    }
  };

  if (isSubLoading) return <div style={{ padding: '1rem', color: '#64748b' }}>Loading IPAM Dashboard...</div>;
  if (subError) return <div style={{ padding: '1rem', color: '#ef4444' }}>Error loading IPAM summary.</div>;

  const totalUsable = subnets?.reduce((acc, s) => acc + s.usable_ips, 0) || 0;
  const totalAllocated = subnets?.reduce((acc, s) => acc + s.allocated_ips, 0) || 0;
  const avgUtil = totalUsable > 0 ? ((totalAllocated / totalUsable) * 100).toFixed(1) : '0';

  return (
    <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.5rem', marginBottom: '2rem' }}>
      <h3 style={{ marginTop: 0, color: '#0f172a', fontSize: '1.2rem' }}>IP Address Management (IPAM)</h3>

      {/* Conflicts Banner Alert */}
      {conflicts && conflicts.length > 0 && (
        <div style={{ marginBottom: '1.5rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '1rem' }}>
          <div style={{ fontWeight: 700, color: '#991b1b', fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            ⚠️ IPAM Conflict Alert ({conflicts.length} conflict(s) detected)
          </div>
          {conflicts.map((c, idx) => (
            <div key={idx} style={{ background: '#ffffff', borderLeft: '4px solid #dc2626', padding: '0.5rem 0.75rem', marginBottom: '0.4rem', borderRadius: '0 4px 4px 0', fontSize: '0.85rem' }}>
              <strong style={{ color: '#b91c1c' }}>[{c.conflict_type}]</strong> {c.description}
            </div>
          ))}
        </div>
      )}

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Active Subnets</div>
          <div style={{ fontWeight: 700, fontSize: '1.25rem', color: '#0f172a' }}>{subnets?.length || 0}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Total Usable IPs</div>
          <div style={{ fontWeight: 700, fontSize: '1.25rem', color: '#0284c7' }}>{totalUsable.toLocaleString()}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Allocated IP Endpoints</div>
          <div style={{ fontWeight: 700, fontSize: '1.25rem', color: '#16a34a' }}>{totalAllocated}</div>
        </div>
        <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>Overall Pool Utilization</div>
          <div style={{ fontWeight: 700, fontSize: '1.25rem', color: '#7c3aed' }}>{avgUtil}%</div>
        </div>
      </div>

      {/* Subnet Utilization Table */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', color: '#334155' }}>Subnet Pools & Utilization Map</h4>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
              <th style={{ padding: '0.6rem 1rem' }}>Subnet CIDR</th>
              <th style={{ padding: '0.6rem 1rem' }}>Network Name</th>
              <th style={{ padding: '0.6rem 1rem' }}>Host / Location</th>
              <th style={{ padding: '0.6rem 1rem' }}>Gateway</th>
              <th style={{ padding: '0.6rem 1rem' }}>Usable Hosts</th>
              <th style={{ padding: '0.6rem 1rem' }}>Allocated</th>
              <th style={{ padding: '0.6rem 1rem' }}>Utilization</th>
            </tr>
          </thead>
          <tbody>
            {subnets && subnets.length > 0 ? (
              subnets.map((sub, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.6rem 1rem', fontFamily: 'monospace', fontWeight: 600, color: '#0369a1' }}>{sub.subnet}</td>
                  <td style={{ padding: '0.6rem 1rem', fontWeight: 600 }}>{sub.network_name}</td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600 }}>
                      🖥️ {sub.host_name || sub.host_id || 'local-docker-host'}
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 1rem', fontFamily: 'monospace', color: '#64748b' }}>{sub.gateway || 'N/A'}</td>
                  <td style={{ padding: '0.6rem 1rem' }}>{sub.usable_ips.toLocaleString()}</td>
                  <td style={{ padding: '0.6rem 1rem' }}>{sub.allocated_ips}</td>
                  <td style={{ padding: '0.6rem 1rem', width: '160px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${Math.max(2, sub.utilization_percentage)}%`, height: '100%', background: sub.utilization_percentage > 80 ? '#ef4444' : '#22c55e' }} />
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b', minWidth: '35px' }}>{sub.utilization_percentage}%</span>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8' }}>No active subnets found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Interactive Subnet Validator Tool */}
      <div style={{ background: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', padding: '1rem' }}>
        <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: '#0f172a' }}>Subnet & Static IP Allocation Validator</h4>
        <form onSubmit={handleValidate} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="text"
            required
            placeholder="Subnet CIDR (e.g. 172.30.0.0/16)"
            value={valSubnet}
            onChange={(e) => setValSubnet(e.target.value)}
            style={{ padding: '0.45rem 0.75rem', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.85rem', flex: 1 }}
          />
          <input
            type="text"
            placeholder="Requested Static IP (Optional)"
            value={valIp}
            onChange={(e) => setValIp(e.target.value)}
            style={{ padding: '0.45rem 0.75rem', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.85rem', flex: 1 }}
          />
          <button
            type="submit"
            style={{ background: '#2563eb', color: '#ffffff', border: 'none', padding: '0.45rem 1rem', borderRadius: '4px', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Validate Bounds
          </button>
        </form>

        {valResult && (
          <div style={{ marginTop: '0.75rem', background: valResult.is_valid ? '#f0fdf4' : '#fef2f2', border: `1px solid ${valResult.is_valid ? '#bbf7d0' : '#fecaca'}`, padding: '0.75rem', borderRadius: '4px', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 700, color: valResult.is_valid ? '#166534' : '#991b1b' }}>
              {valResult.is_valid ? '✅ Allocation Valid' : '❌ Allocation Invalid'}
            </div>
            {valResult.network_address && (
              <div style={{ color: '#475569', marginTop: '0.25rem' }}>
                Network Addr: <code>{valResult.network_address}</code> | Broadcast Addr: <code>{valResult.broadcast_address}</code> | Usable Hosts: <strong>{valResult.usable_ips}</strong>
              </div>
            )}
            {valResult.errors && valResult.errors.length > 0 && (
              <ul style={{ margin: '0.4rem 0 0 0', paddingLeft: '1.2rem', color: '#b91c1c' }}>
                {valResult.errors.map((err: string, i: number) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
