import React, { useState, useEffect } from 'react';

export interface GitOpsRepository {
  id: string;
  name: string;
  repo_url: string;
  branch: string;
  manifest_path: string;
  sync_interval_seconds: number;
  auto_reconcile_low_risk: boolean;
  last_sync_status: 'SYNCED' | 'OUT_OF_SYNC' | 'SYNCING' | 'FAILED';
  last_commit_hash?: string;
  last_synced_at?: string;
  created_at: string;
}

export interface GitSyncResult {
  repository_id: string;
  status: string;
  commit_hash: string;
  drifts_found: number;
  actions_generated: number;
  reconciliation_job_id?: string;
  auto_reconciled: boolean;
  message: string;
}

export const GitOpsManagement: React.FC = () => {
  const [repositories, setRepositories] = useState<GitOpsRepository[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [syncingRepoId, setSyncingRepoId] = useState<string | null>(null);
  const [syncResults, setSyncResults] = useState<Record<string, GitSyncResult>>({});

  // Form State
  const [name, setName] = useState<string>('Production Network Manifests');
  const [repoUrl, setRepoUrl] = useState<string>('https://github.com/org/net-control-plane-manifests');
  const [branch, setBranch] = useState<string>('main');
  const [manifestPath, setManifestPath] = useState<string>('deployment/network-manifest.yaml');
  const [syncInterval, setSyncInterval] = useState<number>(300);
  const [autoReconcile, setAutoReconcile] = useState<boolean>(true);
  const [adding, setAdding] = useState<boolean>(false);

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': 'admin',
    'X-User-Id': 'admin-user',
  });

  const fetchRepositories = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/gitops/repositories', { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setRepositories(data);
      }
    } catch (err) {
      console.error('Failed to fetch GitOps repositories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
  }, []);

  const handleRegisterRepo = async () => {
    setAdding(true);
    try {
      const res = await fetch('/api/v1/gitops/repositories', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          name,
          repo_url: repoUrl,
          branch,
          manifest_path: manifestPath,
          sync_interval_seconds: Number(syncInterval),
          auto_reconcile_low_risk: autoReconcile,
        }),
      });

      if (!res.ok) throw new Error('Failed to register repository');
      await fetchRepositories();
      setName('');
      setRepoUrl('');
    } catch (err: any) {
      alert(`Registration Error: ${err.message}`);
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteRepo = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/gitops/repositories/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to delete repository');
      await fetchRepositories();
    } catch (err: any) {
      alert(`Delete Error: ${err.message}`);
    }
  };

  const handleSyncNow = async (id: string) => {
    setSyncingRepoId(id);
    try {
      const res = await fetch(`/api/v1/gitops/repositories/${id}/sync`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Sync failed');
      const data: GitSyncResult = await res.json();
      setSyncResults((prev) => ({ ...prev, [id]: data }));
      await fetchRepositories();
    } catch (err: any) {
      alert(`Sync Error: ${err.message}`);
    } finally {
      setSyncingRepoId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SYNCED':
        return { bg: '#dcfce7', color: '#166534', border: '#86efac', label: '✅ SYNCED' };
      case 'OUT_OF_SYNC':
        return { bg: '#fef3c7', color: '#92400e', border: '#fcd34d', label: '⚠️ OUT OF SYNC' };
      case 'SYNCING':
        return { bg: '#e0f2fe', color: '#0369a1', border: '#7dd3fc', label: '⚡ SYNCING...' };
      default:
        return { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5', label: '❌ FAILED' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Registration Form */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', color: '#0f172a' }}>
          ➕ Register GitOps Manifest Repository
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
              Repository Name:
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Production Fleet Network"
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
              Git Repository URL:
            </label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/org/manifests"
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
              Branch:
            </label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
              Manifest Path:
            </label>
            <input
              type="text"
              value={manifestPath}
              onChange={(e) => setManifestPath(e.target.value)}
              placeholder="deployment/network-manifest.yaml"
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
              Sync Interval (seconds):
            </label>
            <input
              type="number"
              value={syncInterval}
              onChange={(e) => setSyncInterval(Number(e.target.value))}
              style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', paddingTop: '1.2rem' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoReconcile}
                onChange={(e) => setAutoReconcile(e.target.checked)}
              />
              Auto-Reconcile Low-Risk Actions
            </label>
          </div>
        </div>

        <button
          onClick={handleRegisterRepo}
          disabled={adding}
          style={{
            background: '#16a34a',
            color: '#ffffff',
            border: 'none',
            padding: '0.65rem 1.4rem',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          {adding ? 'Registering Repository...' : '💾 Register Repository'}
        </button>
      </div>

      {/* Repositories List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {repositories.length === 0 ? (
          <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            No GitOps repositories registered yet. Add a Git HTTPS repository above to enable automated continuous sync.
          </div>
        ) : (
          repositories.map((repo) => {
            const badge = getStatusBadge(repo.last_sync_status);
            const syncRes = syncResults[repo.id];
            return (
              <div
                key={repo.id}
                style={{
                  background: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '1.25rem 1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#0f172a' }}>{repo.name}</span>
                    <span style={{ background: badge.bg, color: badge.color, border: `1px solid ${badge.border}`, fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '12px', fontWeight: 700 }}>
                      {badge.label}
                    </span>
                    {repo.auto_reconcile_low_risk && (
                      <span style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '12px', fontWeight: 600 }}>
                        ⚡ Auto-Reconcile Enabled
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => handleSyncNow(repo.id)}
                      disabled={syncingRepoId === repo.id}
                      style={{
                        background: '#0284c7',
                        color: '#ffffff',
                        border: 'none',
                        padding: '0.5rem 1rem',
                        borderRadius: '6px',
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                      }}
                    >
                      {syncingRepoId === repo.id ? '⚡ Syncing Repository...' : '⚡ Sync Now'}
                    </button>
                    <button
                      onClick={() => handleDeleteRepo(repo.id)}
                      style={{
                        background: '#ef4444',
                        color: '#ffffff',
                        border: 'none',
                        padding: '0.5rem 0.85rem',
                        borderRadius: '6px',
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                      }}
                    >
                      🗑️ Unregister
                    </button>
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', color: '#64748b', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                  <span>URL: <code style={{ color: '#0284c7' }}>{repo.repo_url}</code></span>
                  <span>Branch: <code>{repo.branch}</code></span>
                  <span>Manifest: <code>{repo.manifest_path}</code></span>
                  <span>Interval: <strong>{repo.sync_interval_seconds}s</strong></span>
                  {repo.last_commit_hash && <span>Commit: <code>{repo.last_commit_hash}</code></span>}
                </div>

                {syncRes && (
                  <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '0.75rem 1rem', fontSize: '0.8rem' }}>
                    <div style={{ fontWeight: 700, color: syncRes.drifts_found > 0 ? '#92400e' : '#166534' }}>
                      {syncRes.message}
                    </div>
                    <div style={{ color: '#475569', marginTop: '0.2rem' }}>
                      Commit Hash: <code>{syncRes.commit_hash}</code> | Drifts Found: <strong>{syncRes.drifts_found}</strong> | Actions: <strong>{syncRes.actions_generated}</strong> | Auto-Reconciled: <strong>{syncRes.auto_reconciled ? 'YES' : 'NO'}</strong>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
