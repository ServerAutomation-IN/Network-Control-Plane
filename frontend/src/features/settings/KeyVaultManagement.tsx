import React, { useState } from 'react';

export interface KeyVaultTestResult {
  status: 'HEALTHY' | 'UNHEALTHY';
  provider: string;
  url?: string;
  latency_ms: number;
  details: Record<string, any>;
  message: string;
}

export const KeyVaultManagement: React.FC = () => {
  type VaultType = 'vault' | 'aws_secrets' | 'azure_vault' | 'local';
  const [selectedVault, setSelectedVault] = useState<VaultType>('vault');

  // Form State
  const [vaultUrl, setVaultUrl] = useState<string>('http://localhost:8200');
  const [tokenOrSecret, setTokenOrSecret] = useState<string>('root-token');
  const [mountPoint, setMountPoint] = useState<string>('secret');
  const [region, setRegion] = useState<string>('us-east-1');
  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<KeyVaultTestResult | null>(null);

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': 'admin',
    'X-User-Id': 'admin-user',
  });

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const res = await fetch('/api/v1/secrets/test', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          config: {
            provider_type: selectedVault,
            vault_url: vaultUrl,
            token_or_secret: tokenOrSecret,
            mount_point: mountPoint,
            region,
          },
        }),
      });

      if (!res.ok) throw new Error('Key Vault verification call failed.');
      const data: KeyVaultTestResult = await res.json();
      setTestResult(data);
    } catch (err: any) {
      setTestResult({
        status: 'UNHEALTHY',
        provider: selectedVault,
        url: vaultUrl,
        latency_ms: 0,
        details: { error: err.message },
        message: `Connection failed: ${err.message}`,
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1.15rem', color: '#0f172a' }}>
          🔑 Enterprise Key Vault & Zero-Trust Secrets Management
        </h3>
        <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
          Dynamic secret resolution, HSM-backed encryption, and zero static credential storage across cloud VPCs & hypervisors.
        </p>
      </div>

      {/* Provider Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        {[
          { id: 'vault', title: '🛡️ HashiCorp Vault', subtitle: 'KV v2 & Dynamic Lease Engine', badge: 'FIPS 140-2 Level 3' },
          { id: 'aws_secrets', title: '☁️ AWS Secrets Manager', subtitle: 'AWS KMS & STS Temporary Tokens', badge: 'KMS Encrypted' },
          { id: 'azure_vault', title: '🔷 Azure Key Vault', subtitle: 'HSM-Backed & Managed Identity', badge: 'Azure Managed' },
          { id: 'local', title: '🔐 Local Fernet AES-128', subtitle: 'Standalone Encrypted Fallback', badge: 'Dev Mode' },
        ].map((v) => (
          <div
            key={v.id}
            onClick={() => {
              setSelectedVault(v.id as any);
              setTestResult(null);
              if (v.id === 'vault') {
                setVaultUrl('http://localhost:8200');
                setMountPoint('secret');
              }
              if (v.id === 'azure_vault') setVaultUrl('https://ncp-vault.vault.azure.net/');
            }}
            style={{
              padding: '1.25rem',
              borderRadius: '10px',
              border: selectedVault === v.id ? '2px solid #0284c7' : '1px solid #e2e8f0',
              background: selectedVault === v.id ? '#f0f9ff' : '#f8fafc',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>{v.title}</span>
              <span style={{ background: '#dcfce7', color: '#166534', fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', fontWeight: 700 }}>
                {v.badge}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{v.subtitle}</div>
          </div>
        ))}
      </div>

      {/* Form Controls */}
      <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1.25rem' }}>
        <h4 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', color: '#1e293b' }}>
          ⚙️ Vault Endpoint & Authentication Configuration
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
          {selectedVault !== 'local' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                {selectedVault === 'vault' ? 'Vault HTTP Endpoint URL:' : selectedVault === 'azure_vault' ? 'Azure Key Vault URI:' : 'AWS Region Name:'}
              </label>
              <input
                type="text"
                value={selectedVault === 'aws_secrets' ? region : vaultUrl}
                onChange={(e) => selectedVault === 'aws_secrets' ? setRegion(e.target.value) : setVaultUrl(e.target.value)}
                style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
              />
            </div>
          )}

          {selectedVault === 'vault' && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  Vault Access Token / AppRole Secret:
                </label>
                <input
                  type="password"
                  value={tokenOrSecret}
                  onChange={(e) => setTokenOrSecret(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  KV Engine Mount Path:
                </label>
                <input
                  type="text"
                  value={mountPoint}
                  onChange={(e) => setMountPoint(e.target.value)}
                  placeholder="secret"
                  style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>
            </>
          )}
        </div>

        <button
          onClick={handleTestConnection}
          disabled={testing}
          style={{
            background: '#0284c7',
            color: '#ffffff',
            border: 'none',
            padding: '0.65rem 1.4rem',
            borderRadius: '6px',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          {testing ? '⚡ Testing Vault Reachability...' : '⚡ Test Key Vault Connection'}
        </button>
      </div>

      {/* Test Result Card */}
      {testResult && (
        <div
          style={{
            padding: '1.25rem',
            borderRadius: '8px',
            background: testResult.status === 'HEALTHY' ? '#f0fdf4' : '#fef2f2',
            border: testResult.status === 'HEALTHY' ? '1px solid #bbf7d0' : '1px solid #fecaca',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: testResult.status === 'HEALTHY' ? '#166534' : '#991b1b' }}>
              {testResult.status === 'HEALTHY' ? '✅ Key Vault Reachable & Verified' : '❌ Key Vault Connection Failed'}
            </span>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
              Latency: <strong>{testResult.latency_ms} ms</strong>
            </span>
          </div>
          <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#334155' }}>{testResult.message}</p>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontFamily: 'monospace' }}>
            Provider: {testResult.provider}
          </div>
        </div>
      )}

      {/* Secret Reference Syntax Helper Guide */}
      <div style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1rem', fontSize: '0.82rem', color: '#334155' }}>
        <strong style={{ color: '#0f172a' }}>💡 Zero-Trust Secret Reference Syntax:</strong>
        <ul style={{ margin: '0.4rem 0 0 1.2rem', padding: 0 }}>
          <li>HashiCorp Vault: <code style={{ color: '#0284c7' }}>vault://secret/data/ncp/vcenter</code></li>
          <li>AWS Secrets Manager: <code style={{ color: '#0284c7' }}>aws-secret://prod/ncp/aws-creds</code></li>
          <li>Azure Key Vault: <code style={{ color: '#0284c7' }}>azure-vault://ncp-azure-sp-key</code></li>
        </ul>
      </div>
    </div>
  );
};
