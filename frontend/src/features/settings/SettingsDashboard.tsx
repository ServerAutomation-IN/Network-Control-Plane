import React, { useState, useEffect } from 'react';
import { BackgroundQueueDashboard } from '../tasks/BackgroundQueueDashboard';
import { KeyVaultManagement } from './KeyVaultManagement';
import { UserManagement } from './UserManagement';

export interface ProviderTestResult {
  status: 'REACHABLE' | 'UNREACHABLE';
  provider_type: string;
  endpoint_url: string;
  latency_ms: number;
  details: Record<string, any>;
  message: string;
}

export interface LLMTestResult {
  status: 'CONNECTED' | 'FAILED';
  provider_used: string;
  model: string;
  latency_ms: number;
  sample_response: string;
  error_message?: string;
}

export interface WebhookSubscription {
  id: string;
  name: string;
  channel_type: string;
  target_url: string;
  subscribed_events: string[];
  enabled: boolean;
  created_at: string;
}

export interface WebhookTestResult {
  status: 'DELIVERED' | 'FAILED';
  status_code: number;
  latency_ms: number;
  message: string;
  signature_header: string;
}

export interface SSOProvider {
  id: string;
  name: string;
  issuer_url: string;
  client_id: string;
  enabled: boolean;
}

export const SettingsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'providers' | 'llm' | 'sso' | 'users' | 'webhooks' | 'queue' | 'vault'>('providers');
  const [selectedProvider, setSelectedProvider] = useState<'hyperv' | 'vmware' | 'nutanix' | 'aws' | 'azure' | 'gcp'>('hyperv');

  // Provider Form State
  const [providerEndpoint, setProviderEndpoint] = useState<string>('hyperv-scvmm.corp.internal');
  const [providerRegion, setProviderRegion] = useState<string>('datacenter-1');
  const [providerUsername, setProviderUsername] = useState<string>('CORP\\svc-netadmin');
  const [providerSecret, setProviderSecret] = useState<string>('••••••••••••••••');
  const [testingProvider, setTestingProvider] = useState<boolean>(false);
  const [providerResult, setProviderResult] = useState<ProviderTestResult | null>(null);

  // LLM Form State per provider
  type LLMProviderType = 'ollama' | 'openai' | 'azure' | 'anthropic';
  const [llmProvider, setLLMProvider] = useState<LLMProviderType>('ollama');
  const [providerConfigs, setProviderConfigs] = useState<Record<LLMProviderType, { url: string; model: string; apiKey: string }>>({
    ollama: { url: 'http://localhost:11434', model: 'llama3', apiKey: '' },
    openai: { url: 'https://api.openai.com/v1', model: 'gpt-4o', apiKey: '' },
    azure: { url: 'https://your-resource.openai.azure.com/', model: 'gpt-4o-deployment', apiKey: '' },
    anthropic: { url: 'https://api.anthropic.com/v1', model: 'claude-3-5-sonnet-20241022', apiKey: '' },
  });
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [testingLLM, setTestingLLM] = useState<boolean>(false);
  const [llmResult, setLLMResult] = useState<LLMTestResult | null>(null);
  const [savingSettings, setSavingSettings] = useState<boolean>(false);
  const [saveToast, setSaveToast] = useState<string | null>(null);

  // SSO Form & State
  const [ssoProviders, setSsoProviders] = useState<SSOProvider[]>([]);
  const [selectedSsoProvider, setSelectedSsoProvider] = useState<string>('keycloak');
  const [simulatedUserRole, setSimulatedUserRole] = useState<'admin' | 'operator' | 'viewer'>('admin');
  const [ssoTokenResult, setSsoTokenResult] = useState<any>(null);
  const [testingSso, setTestingSso] = useState<boolean>(false);

  // Webhooks State
  const [webhooks, setWebhooks] = useState<WebhookSubscription[]>([]);
  const [newWhName, setNewWhName] = useState<string>('Slack Network Alerts');
  const [newWhChannel, setNewWhChannel] = useState<string>('slack');
  const [newWhUrl, setNewWhUrl] = useState<string>('https://hooks.slack.com/services/T00/B00/X00');
  const [newWhSecret, setNewWhSecret] = useState<string>('whsec_secret_token_123');
  const [newWhEvents, setNewWhEvents] = useState<string>('AUDIT_EVENT,DRIFT_DETECTED');
  const [addingWh, setAddingWh] = useState<boolean>(false);
  const [testingWhId, setTestingWhId] = useState<string | null>(null);
  const [webhookTestResults, setWebhookTestResults] = useState<Record<string, WebhookTestResult>>({});

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': 'admin',
    'X-User-Id': 'admin-user',
  });

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await fetch('/api/v1/settings', { headers: getHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        if (data.active_llm_provider) {
          setLLMProvider(data.active_llm_provider as LLMProviderType);
        }
        setProviderConfigs((prev) => ({
          ollama: {
            url: data.ollama_base_url || prev.ollama.url,
            model: data.ollama_model || prev.ollama.model,
            apiKey: prev.ollama.apiKey,
          },
          openai: {
            url: data.openai_base_url || prev.openai.url,
            model: data.openai_model || prev.openai.model,
            apiKey: prev.openai.apiKey,
          },
          azure: {
            url: data.azure_base_url || prev.azure.url,
            model: data.azure_model || prev.azure.model,
            apiKey: prev.azure.apiKey,
          },
          anthropic: {
            url: data.anthropic_base_url || prev.anthropic.url,
            model: data.anthropic_model || prev.anthropic.model,
            apiKey: prev.anthropic.apiKey,
          },
        }));
      } catch (err) {
        console.error('Failed to load system settings:', err);
      }
    };
    loadSettings();
    fetchSsoProviders();
    fetchWebhooks();
  }, []);

  const fetchSsoProviders = async () => {
    try {
      const res = await fetch('/api/v1/auth/providers', { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setSsoProviders(data);
      }
    } catch (err) {
      console.error('Failed to fetch SSO providers:', err);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const res = await fetch('/api/v1/webhooks', { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setWebhooks(data);
      }
    } catch (err) {
      console.error('Failed to fetch webhooks:', err);
    }
  };

  const updateActiveConfig = (field: 'url' | 'model' | 'apiKey', val: string) => {
    setProviderConfigs((prev) => ({
      ...prev,
      [llmProvider]: {
        ...prev[llmProvider],
        [field]: val,
      },
    }));
  };

  const activeLLMCfg = providerConfigs[llmProvider];

  const handleTestProviderEndpoint = async () => {
    setTestingProvider(true);
    setProviderResult(null);

    try {
      const res = await fetch('/api/v1/settings/test-provider-endpoint', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          provider_type: selectedProvider,
          endpoint_url: providerEndpoint,
          region_or_zone: providerRegion,
          credentials: { username: providerUsername, secret: providerSecret },
        }),
      });

      if (!res.ok) throw new Error('Endpoint verification call failed.');
      const data: ProviderTestResult = await res.json();
      setProviderResult(data);
    } catch (err: any) {
      setProviderResult({
        status: 'UNREACHABLE',
        provider_type: selectedProvider,
        endpoint_url: providerEndpoint,
        latency_ms: 0,
        details: { error: err.message },
        message: `Endpoint verification failed: ${err.message}`,
      });
    } finally {
      setTestingProvider(false);
    }
  };

  const handleTestLLMConnection = async () => {
    setTestingLLM(true);
    setLLMResult(null);

    try {
      const res = await fetch('/api/v1/settings/test-llm', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          provider_name: llmProvider,
          base_url: activeLLMCfg.url,
          model: activeLLMCfg.model,
          api_key: activeLLMCfg.apiKey,
        }),
      });

      if (!res.ok) throw new Error('LLM verification call failed.');
      const data: LLMTestResult = await res.json();
      setLLMResult(data);
    } catch (err: any) {
      setLLMResult({
        status: 'FAILED',
        provider_used: llmProvider,
        model: activeLLMCfg.model,
        latency_ms: 0,
        sample_response: '',
        error_message: `LLM Connection failed: ${err.message}`,
      });
    } finally {
      setTestingLLM(false);
    }
  };

  const handleSaveSystemSettings = async () => {
    setSavingSettings(true);
    setSaveToast(null);

    try {
      const res = await fetch('/api/v1/settings', {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({
          active_llm_provider: llmProvider,
          ollama_base_url: providerConfigs.ollama.url,
          ollama_model: providerConfigs.ollama.model,
          openai_base_url: providerConfigs.openai.url,
          openai_model: providerConfigs.openai.model,
          openai_api_key: providerConfigs.openai.apiKey || undefined,
          azure_base_url: providerConfigs.azure.url,
          azure_model: providerConfigs.azure.model,
          azure_api_key: providerConfigs.azure.apiKey || undefined,
          anthropic_base_url: providerConfigs.anthropic.url,
          anthropic_model: providerConfigs.anthropic.model,
          anthropic_api_key: providerConfigs.anthropic.apiKey || undefined,
        }),
      });

      if (!res.ok) throw new Error('Failed to save settings.');
      setSaveToast('✅ System Settings successfully saved and persisted to PostgreSQL!');
      setTimeout(() => setSaveToast(null), 4000);
    } catch (err: any) {
      alert(`Save Error: ${err.message}`);
    } finally {
      setSavingSettings(false);
    }
  };

  const handleSimulateSsoLogin = async () => {
    setTestingSso(true);
    setSsoTokenResult(null);
    try {
      const res = await fetch('/api/v1/auth/login/direct', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          username: `sso-user-${selectedSsoProvider}`,
          password: 'mock-password',
          requested_role: simulatedUserRole,
        }),
      });

      if (!res.ok) throw new Error('SSO authentication callback failed');
      const data = await res.json();
      setSsoTokenResult(data);
    } catch (err: any) {
      alert(`SSO Login Simulation failed: ${err.message}`);
    } finally {
      setTestingSso(false);
    }
  };

  const handleAddWebhook = async () => {
    setAddingWh(true);
    try {
      const res = await fetch('/api/v1/webhooks', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          name: newWhName,
          channel_type: newWhChannel,
          target_url: newWhUrl,
          secret_token: newWhSecret,
          subscribed_events: newWhEvents.split(',').map((s) => s.trim()),
          enabled: true,
        }),
      });

      if (!res.ok) throw new Error('Failed to add webhook');
      await fetchWebhooks();
      setNewWhName('');
      setNewWhUrl('');
    } catch (err: any) {
      alert(`Add Webhook Error: ${err.message}`);
    } finally {
      setAddingWh(false);
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/webhooks/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to delete webhook');
      await fetchWebhooks();
    } catch (err: any) {
      alert(`Delete Error: ${err.message}`);
    }
  };

  const handleTestWebhookPing = async (id: string, url: string) => {
    setTestingWhId(id);
    try {
      const res = await fetch(`/api/v1/webhooks/${id}/test`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Test delivery call failed');
      const data: WebhookTestResult = await res.json();
      setWebhookTestResults((prev) => ({ ...prev, [id]: data }));
    } catch (err: any) {
      setWebhookTestResults((prev) => ({
        ...prev,
        [id]: {
          status: 'FAILED',
          status_code: 500,
          latency_ms: 0,
          message: err.message,
          signature_header: 'N/A',
        },
      }));
    } finally {
      setTestingWhId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div style={{ background: '#0f172a', color: '#ffffff', padding: '1.5rem 2rem', borderRadius: '12px', border: '1px solid #1e293b', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              ⚙️ System Settings & Enterprise Integrations
            </h2>
            <p style={{ margin: '0.3rem 0 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
              Manage Cloud VPCs, Enterprise Hypervisors, LLM AI, SSO Identity Providers & Webhook Channels
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', background: '#1e293b', padding: '0.3rem', borderRadius: '8px', border: '1px solid #334155' }}>
            <button
              onClick={() => setActiveTab('providers')}
              style={{
                background: activeTab === 'providers' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              ☁️ Cloud & Hypervisor Providers
            </button>
            <button
              onClick={() => setActiveTab('llm')}
              style={{
                background: activeTab === 'llm' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              🤖 LLM Connection Panel
            </button>
            <button
              onClick={() => setActiveTab('sso')}
              style={{
                background: activeTab === 'sso' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              🔐 SSO & Authentication
            </button>
            <button
              onClick={() => setActiveTab('users')}
              style={{
                background: activeTab === 'users' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              👥 Users & Role Governance
            </button>
            <button
              onClick={() => setActiveTab('webhooks')}
              style={{
                background: activeTab === 'webhooks' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              🔔 Webhook Channels
            </button>
            <button
              onClick={() => setActiveTab('queue')}
              style={{
                background: activeTab === 'queue' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              ⚡ Execution Queue
            </button>
            <button
              onClick={() => setActiveTab('vault')}
              style={{
                background: activeTab === 'vault' ? '#0284c7' : 'transparent',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              🔑 Key Vault & Secrets Engine
            </button>
          </div>
        </div>
      </div>

      {saveToast && (
        <div style={{ background: '#dcfce7', color: '#166534', border: '1px solid #86efac', padding: '0.85rem 1.25rem', borderRadius: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
          {saveToast}
        </div>
      )}

      {/* Tab 1: Provider Credentials Manager */}
      {activeTab === 'providers' && (
        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.15rem', color: '#0f172a' }}>
            Provider Credentials Manager
          </h3>

          {/* Provider Selector Pills */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
            {[
              { id: 'hyperv', label: '🪟 Microsoft Hyper-V / SCVMM' },
              { id: 'vmware', label: '🖥️ VMware vSphere & NSX-T' },
              { id: 'nutanix', label: '⚡ Nutanix AHV' },
              { id: 'aws', label: '☁️ AWS Cloud VPC' },
              { id: 'azure', label: '🔷 Azure Virtual Network' },
              { id: 'gcp', label: '🌐 GCP Cloud VPC' },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setSelectedProvider(p.id as any);
                  setProviderResult(null);
                  if (p.id === 'hyperv') setProviderEndpoint('hyperv-scvmm.corp.internal');
                  if (p.id === 'vmware') setProviderEndpoint('vcenter.corp.internal');
                  if (p.id === 'nutanix') setProviderEndpoint('prism.corp.internal');
                  if (p.id === 'aws') setProviderEndpoint('us-east-1');
                  if (p.id === 'azure') setProviderEndpoint('eastus');
                  if (p.id === 'gcp') setProviderEndpoint('gcp-prod-project');
                }}
                style={{
                  background: selectedProvider === p.id ? '#f0f9ff' : '#f8fafc',
                  border: selectedProvider === p.id ? '2px solid #0284c7' : '1px solid #cbd5e1',
                  color: selectedProvider === p.id ? '#0369a1' : '#475569',
                  padding: '0.6rem 1rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Configuration Form Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                Management API Endpoint / Hostname:
              </label>
              <input
                type="text"
                value={providerEndpoint}
                onChange={(e) => setProviderEndpoint(e.target.value)}
                placeholder="e.g. hyperv-scvmm.corp.internal or 10.40.0.10"
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                Datacenter Region / Zone:
              </label>
              <input
                type="text"
                value={providerRegion}
                onChange={(e) => setProviderRegion(e.target.value)}
                placeholder="e.g. datacenter-east, us-east-1"
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                Username / Service Account ID:
              </label>
              <input
                type="text"
                value={providerUsername}
                onChange={(e) => setProviderUsername(e.target.value)}
                placeholder="e.g. CORP\\netadmin or client_id"
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                Secret Access Key / Password / Certificate:
              </label>
              <input
                type="password"
                value={providerSecret}
                onChange={(e) => setProviderSecret(e.target.value)}
                placeholder="Encrypted at rest with Fernet AES-128"
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          {/* Action Bar */}
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button
              onClick={handleTestProviderEndpoint}
              disabled={testingProvider}
              style={{
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {testingProvider ? '⚡ Testing Endpoint Reachability...' : '⚡ Test Endpoint Reachability'}
            </button>
          </div>

          {/* Provider Test Result Card */}
          {providerResult && (
            <div
              style={{
                marginTop: '1.5rem',
                padding: '1.25rem',
                borderRadius: '8px',
                background: providerResult.status === 'REACHABLE' ? '#f0fdf4' : '#fef2f2',
                border: providerResult.status === 'REACHABLE' ? '1px solid #bbf7d0' : '1px solid #fecaca',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: providerResult.status === 'REACHABLE' ? '#166534' : '#991b1b' }}>
                  {providerResult.status === 'REACHABLE' ? '✅ Endpoint Online & Verified' : '❌ Reachability Verification Failed'}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                  Latency: <strong>{providerResult.latency_ms} ms</strong>
                </span>
              </div>
              <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#334155' }}>{providerResult.message}</p>
              {providerResult.status === 'REACHABLE' && providerResult.details && (
                <div style={{ fontSize: '0.8rem', color: '#475569', display: 'flex', gap: '1.5rem' }}>
                  <span>Discovered Networks: <strong>{providerResult.details.networks_discovered || 0}</strong></span>
                  <span>Discovered Workloads: <strong>{providerResult.details.workloads_discovered || 0}</strong></span>
                  <span>Version: <strong>{providerResult.details.version || 'N/A'}</strong></span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: LLM Connection Settings Panel */}
      {activeTab === 'llm' && (
        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.15rem', color: '#0f172a' }}>
            LLM Connection Settings Panel
          </h3>

          {/* LLM Provider Selector Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { id: 'ollama', title: '🦙 Ollama (Local)', desc: 'Local private inference (Llama, DeepSeek, Qwen)' },
              { id: 'openai', title: '🟢 OpenAI', desc: 'OpenAI API (GPT-4o, o1, o3-mini series)' },
              { id: 'azure', title: '🔷 Azure OpenAI', desc: 'Enterprise Azure OpenAI deployment' },
              { id: 'anthropic', title: '🟧 Anthropic', desc: 'Anthropic API (Claude 3.7 / 3.5 Sonnet, Haiku)' },
            ].map((m) => (
              <div
                key={m.id}
                onClick={() => {
                  setLLMProvider(m.id as any);
                  setLLMResult(null);
                }}
                style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  border: llmProvider === m.id ? '2px solid #2563eb' : '1px solid #cbd5e1',
                  background: llmProvider === m.id ? '#eff6ff' : '#f8fafc',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a', marginBottom: '0.25rem' }}>{m.title}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{m.desc}</div>
              </div>
            ))}
          </div>

          {/* Form Controls */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                {llmProvider === 'ollama'
                  ? 'Ollama Base Endpoint URL:'
                  : llmProvider === 'openai'
                  ? 'OpenAI API Base Endpoint URL:'
                  : llmProvider === 'azure'
                  ? 'Azure OpenAI Deployment URL:'
                  : 'Anthropic API Base Endpoint URL:'}
              </label>
              <input
                type="text"
                value={activeLLMCfg.url}
                onChange={(e) => updateActiveConfig('url', e.target.value)}
                placeholder={
                  llmProvider === 'ollama'
                    ? 'http://localhost:11434'
                    : llmProvider === 'openai'
                    ? 'https://api.openai.com/v1'
                    : llmProvider === 'azure'
                    ? 'https://your-resource.openai.azure.com/'
                    : 'https://api.anthropic.com/v1'
                }
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                {llmProvider === 'ollama'
                  ? 'Model Identifier / Tag:'
                  : llmProvider === 'openai'
                  ? 'OpenAI Model (e.g., gpt-4o, o3-mini):'
                  : llmProvider === 'azure'
                  ? 'Azure Model / Deployment Name:'
                  : 'Anthropic Model (e.g., claude-3-7-sonnet, claude-3-5-sonnet):'}
              </label>
              <input
                type="text"
                value={activeLLMCfg.model}
                onChange={(e) => updateActiveConfig('model', e.target.value)}
                placeholder={
                  llmProvider === 'ollama'
                    ? 'qwen2.5-coder:7b, llama3.3, deepseek-r1'
                    : llmProvider === 'openai'
                    ? 'gpt-4o'
                    : llmProvider === 'azure'
                    ? 'gpt-4o-deployment'
                    : 'claude-3-7-sonnet-20250219'
                }
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>

            {llmProvider !== 'ollama' && (
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.4rem' }}>
                  API Key / Secret Token:
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={activeLLMCfg.apiKey}
                    onChange={(e) => updateActiveConfig('apiKey', e.target.value)}
                    placeholder="Enter provider API Key (sk-...)"
                    style={{ flex: 1, padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.85rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    style={{ padding: '0.65rem 1rem', border: '1px solid #cbd5e1', background: '#f8fafc', borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                    {showApiKey ? '🔒 Hide' : '👁️ Show'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={handleTestLLMConnection}
              disabled={testingLLM}
              style={{
                background: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {testingLLM ? '🧪 Testing LLM Connection...' : '🧪 Test LLM Connection'}
            </button>

            <button
              onClick={handleSaveSystemSettings}
              disabled={savingSettings}
              style={{
                background: '#16a34a',
                color: '#ffffff',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              {savingSettings ? 'Saving Settings...' : '💾 Save System Configuration'}
            </button>
          </div>

          {/* LLM Test Result Card */}
          {llmResult && (
            <div
              style={{
                marginTop: '1.5rem',
                padding: '1.25rem',
                borderRadius: '8px',
                background: llmResult.status === 'CONNECTED' ? '#f0fdf4' : '#fef2f2',
                border: llmResult.status === 'CONNECTED' ? '1px solid #bbf7d0' : '1px solid #fecaca',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: llmResult.status === 'CONNECTED' ? '#166534' : '#991b1b' }}>
                  {llmResult.status === 'CONNECTED' ? '✅ LLM Connection Successful' : '❌ LLM Connection Failed'}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                  Provider: <strong>{llmResult.provider_used}</strong> | Latency: <strong>{llmResult.latency_ms} ms</strong>
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: '#1e293b', background: '#ffffff', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                {llmResult.sample_response || llmResult.error_message}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Enterprise SSO & Authentication */}
      {activeTab === 'sso' && (
        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.15rem', color: '#0f172a' }}>
            Enterprise SSO & OIDC / SAML2 Identity Providers
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {ssoProviders.map((provider) => (
              <div
                key={provider.id}
                style={{
                  padding: '1.25rem',
                  borderRadius: '10px',
                  border: selectedSsoProvider === provider.id ? '2px solid #0284c7' : '1px solid #e2e8f0',
                  background: selectedSsoProvider === provider.id ? '#f0f9ff' : '#f8fafc',
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedSsoProvider(provider.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>{provider.name}</span>
                  <span style={{ background: '#dcfce7', color: '#166534', fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
                    OIDC 1.0 Enabled
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#64748b', margin: '0.2rem 0' }}>
                  Issuer: <code style={{ color: '#0284c7' }}>{provider.issuer_url}</code>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  Client ID: <code>{provider.client_id}</code>
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#1e293b' }}>
              ⚡ Interactive SSO JWT Token Issuer & Role Mapping Simulator
            </h4>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginRight: '0.5rem' }}>
                  Target Provider:
                </label>
                <select
                  value={selectedSsoProvider}
                  onChange={(e) => setSelectedSsoProvider(e.target.value)}
                  style={{ padding: '0.5rem 0.85rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                >
                  <option value="keycloak">Keycloak OIDC</option>
                  <option value="okta">Okta SSO</option>
                  <option value="azure-ad">Azure AD (Entra ID)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginRight: '0.5rem' }}>
                  Mapped Platform Role:
                </label>
                <select
                  value={simulatedUserRole}
                  onChange={(e) => setSimulatedUserRole(e.target.value as any)}
                  style={{ padding: '0.5rem 0.85rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                >
                  <option value="admin">admin (Full Admin Privileges)</option>
                  <option value="operator">operator (Provisioning & Mutations)</option>
                  <option value="viewer">viewer (Read-only Inspection)</option>
                </select>
              </div>

              <button
                onClick={handleSimulateSsoLogin}
                disabled={testingSso}
                style={{
                  background: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                {testingSso ? 'Authenticating...' : '🔑 Simulate SSO Callback & Issue JWT'}
              </button>
            </div>

            {ssoTokenResult && (
              <div style={{ marginTop: '1rem', background: '#0f172a', color: '#38bdf8', padding: '1rem', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.8rem', overflowX: 'auto' }}>
                <div style={{ color: '#4ade80', fontWeight: 700, marginBottom: '0.4rem' }}>
                  ✅ Signed JWT Access Token Generated (24h Expiry)
                </div>
                <div>User ID: {ssoTokenResult.user_id}</div>
                <div>Assigned Role: {ssoTokenResult.role}</div>
                <div>IdP Provider: {ssoTokenResult.provider}</div>
                <div style={{ marginTop: '0.5rem', color: '#94a3b8', wordBreak: 'break-all' }}>
                  Bearer Token: {ssoTokenResult.access_token}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Platform Users & Access Governance */}
      {activeTab === 'users' && (
        <UserManagement />
      )}

      {/* Tab 4: Outbound Webhooks & Alerting Channels */}
      {activeTab === 'webhooks' && (
        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.15rem', color: '#0f172a' }}>
            Outbound Webhook & Alerting Channels (HMAC-SHA256 Signed)
          </h3>

          {/* Add Webhook Channel Form */}
          <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#1e293b' }}>
              ➕ Register New Webhook Channel
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  Channel Name:
                </label>
                <input
                  type="text"
                  value={newWhName}
                  onChange={(e) => setNewWhName(e.target.value)}
                  placeholder="Slack Production Ops"
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  Channel Platform:
                </label>
                <select
                  value={newWhChannel}
                  onChange={(e) => setNewWhChannel(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                >
                  <option value="slack">Slack Incoming Webhook</option>
                  <option value="pagerduty">PagerDuty Events V2 API</option>
                  <option value="msteams">Microsoft Teams Connector</option>
                  <option value="generic">Generic REST Webhook Endpoint</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  Destination Target URL:
                </label>
                <input
                  type="text"
                  value={newWhUrl}
                  onChange={(e) => setNewWhUrl(e.target.value)}
                  placeholder="https://hooks.slack.com/services/..."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#475569', marginBottom: '0.3rem' }}>
                  Secret Token (HMAC-SHA256):
                </label>
                <input
                  type="password"
                  value={newWhSecret}
                  onChange={(e) => setNewWhSecret(e.target.value)}
                  placeholder="Secret key for header signature"
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                />
              </div>
            </div>

            <button
              onClick={handleAddWebhook}
              disabled={addingWh}
              style={{
                background: '#16a34a',
                color: '#ffffff',
                border: 'none',
                padding: '0.6rem 1.25rem',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              {addingWh ? 'Registering...' : '💾 Register Webhook Channel'}
            </button>
          </div>

          {/* Webhooks List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {webhooks.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.9rem' }}>
                No active webhook channels configured. Create one above to receive audit & alert events.
              </div>
            ) : (
              webhooks.map((wh) => {
                const testRes = webhookTestResults[wh.id];
                return (
                  <div
                    key={wh.id}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '1.25rem',
                      background: '#ffffff',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '1rem', color: '#0f172a' }}>{wh.name}</span>
                          <span style={{ background: '#e0f2fe', color: '#0369a1', fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600, textTransform: 'uppercase' }}>
                            {wh.channel_type}
                          </span>
                          <span style={{ background: '#dcfce7', color: '#166534', fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
                            ACTIVE
                          </span>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.3rem' }}>
                          URL: <code style={{ color: '#0284c7' }}>{wh.target_url}</code>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleTestWebhookPing(wh.id, wh.target_url)}
                          disabled={testingWhId === wh.id}
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
                          {testingWhId === wh.id ? '⚡ Pinging Target...' : '⚡ Test Delivery Ping'}
                        </button>
                        <button
                          onClick={() => handleDeleteWebhook(wh.id)}
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
                          🗑️ Delete
                        </button>
                      </div>
                    </div>

                    {testRes && (
                      <div
                        style={{
                          marginTop: '1rem',
                          padding: '0.85rem 1rem',
                          borderRadius: '6px',
                          background: testRes.status === 'DELIVERED' ? '#f0fdf4' : '#fef2f2',
                          border: testRes.status === 'DELIVERED' ? '1px solid #bbf7d0' : '1px solid #fecaca',
                          fontSize: '0.8rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: testRes.status === 'DELIVERED' ? '#166534' : '#991b1b' }}>
                          <span>{testRes.status === 'DELIVERED' ? '✅ Ping Delivered' : '❌ Ping Delivery Failed'}</span>
                          <span>HTTP {testRes.status_code} ({testRes.latency_ms} ms)</span>
                        </div>
                        <div style={{ margin: '0.3rem 0', color: '#334155' }}>{testRes.message}</div>
                        <div style={{ color: '#64748b', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                          X-NCP-Signature: {testRes.signature_header}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Background Execution Queue Monitor */}
      {activeTab === 'queue' && (
        <BackgroundQueueDashboard />
      )}

      {/* Tab 6: Key Vault & Enterprise Secrets Engine */}
      {activeTab === 'vault' && (
        <KeyVaultManagement />
      )}
    </div>
  );
};
