import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import { AuthPage } from './features/auth/AuthPage';
import { NetworkList } from './features/networks/NetworkList';
import { NetworkDetail } from './features/networks/NetworkDetail';
import { AuditLogList } from './features/audit/AuditLogList';
import { TopologyCanvas } from './features/topology/TopologyCanvas';
import { IPAMDashboard } from './features/ipam/IPAMDashboard';
import { PolicyDashboard } from './features/policies/PolicyDashboard';
import { DriftDashboard } from './features/drift/DriftDashboard';
import { SettingsDashboard } from './features/settings/SettingsDashboard';
import { AIAssistantDrawer } from './features/ai/AIAssistantDrawer';
import { ConnectHostModal } from './features/topology/ConnectHostModal';
import { LogOut } from 'lucide-react';

type TabType = 'topology' | 'networks' | 'ipam' | 'policies' | 'drift' | 'audit' | 'settings';

const getInitialTab = (): TabType => {
  const hash = window.location.hash.replace('#', '');
  const validTabs: TabType[] = ['topology', 'networks', 'ipam', 'policies', 'drift', 'audit', 'settings'];
  if (validTabs.includes(hash as TabType)) {
    return hash as TabType;
  }
  const saved = localStorage.getItem('ncp_active_tab');
  if (saved && validTabs.includes(saved as TabType)) {
    return saved as TabType;
  }
  return 'topology';
};

const MainDashboard: React.FC = () => {
  const { user, role, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab);
  const [selectedNetworkId, setSelectedNetworkId] = useState<string | null>(null);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState<boolean>(false);

  const handleTabChange = (tab: TabType) => {
    setSelectedNetworkId(null);
    setActiveTab(tab);
    window.location.hash = tab;
    localStorage.setItem('ncp_active_tab', tab);
  };

  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      const validTabs: TabType[] = ['topology', 'networks', 'ipam', 'policies', 'drift', 'audit', 'settings'];
      if (validTabs.includes(hash as TabType)) {
        setActiveTab(hash as TabType);
      }
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const handleSelectNetwork = (id: string) => {
    setSelectedNetworkId(id);
  };

  const handleBackFromInspect = () => {
    setSelectedNetworkId(null);
    handleTabChange('networks');
  };

  return (
    <div style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif', background: '#f8fafc', minHeight: '100vh', color: '#0f172a' }}>
      {/* Top Navbar */}
      <header style={{ background: '#0f172a', color: '#ffffff', borderBottom: '1px solid #1e293b', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '1.25rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Network Control Plane
              </h1>
              <span style={{ background: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
                v1.0.0-GA
              </span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
              Visualize. Manage. Validate. Govern. Automate Workload Networking.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            {/* Host Status Pill */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#1e293b', padding: '0.4rem 0.85rem', borderRadius: '20px', border: '1px solid #334155', fontSize: '0.8rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
              <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Docker Engine ONLINE</span>
            </div>

            {/* Quick Action: Connect Host Button */}
            {(role === 'admin' || role === 'operator') && (
              <button
                onClick={() => setIsConnectModalOpen(true)}
                title="Connect a remote edge host, VM, or cloud server"
                style={{
                  background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '0.4rem 0.85rem',
                  borderRadius: '20px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  boxShadow: '0 2px 4px rgba(2, 132, 199, 0.25)',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>🖥️</span>
                <span>+ Connect Host</span>
              </button>
            )}

            {/* Authenticated User Identity Chip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#1e293b', padding: '0.35rem 0.75rem', borderRadius: '20px', border: '1px solid #334155' }}>
              <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#ffffff' }}>
                {user?.user_id?.charAt(0).toUpperCase() || 'A'}
              </span>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9' }}>
                {user?.user_id || 'admin'}
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '0.15rem 0.45rem',
                  borderRadius: '6px',
                  background: role === 'admin' ? 'rgba(56, 189, 248, 0.15)' : role === 'operator' ? 'rgba(251, 191, 36, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                  color: role === 'admin' ? '#38bdf8' : role === 'operator' ? '#fbbf24' : '#94a3b8',
                }}
              >
                {role}
              </span>
            </div>

            {/* Sign Out Button */}
            <button
              onClick={logout}
              title="Sign Out of Network Control Plane"
              style={{
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#f87171',
                padding: '0.4rem 0.75rem',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                transition: 'all 0.15s ease',
              }}
            >
              <LogOut size={14} />
              Sign Out
            </button>
          </div>
        </div>

        {/* Tab Navigation Bar */}
        <div style={{ maxWidth: '1380px', margin: '0 auto', padding: '0 2rem' }}>
          <nav style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #1e293b', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleTabChange('topology')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'topology' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'topology' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              🗺️ Topology Visualizer
            </button>

            <button
              onClick={() => handleTabChange('networks')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: (activeTab === 'networks' || selectedNetworkId) ? '3px solid #38bdf8' : '3px solid transparent',
                color: (activeTab === 'networks' || selectedNetworkId) ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              🌐 Networks & Workloads
            </button>

            <button
              onClick={() => handleTabChange('ipam')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'ipam' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'ipam' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              🔢 IPAM & Subnets
            </button>

            <button
              onClick={() => handleTabChange('policies')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'policies' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'policies' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              🛡️ Policy & Compliance
            </button>

            <button
              onClick={() => handleTabChange('drift')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'drift' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'drift' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              🔄 GitOps & Drift
            </button>

            <button
              onClick={() => handleTabChange('audit')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'audit' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'audit' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              📜 Immutable Audit Log
            </button>

            <button
              onClick={() => handleTabChange('settings')}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === 'settings' && !selectedNetworkId ? '3px solid #38bdf8' : '3px solid transparent',
                color: activeTab === 'settings' && !selectedNetworkId ? '#38bdf8' : '#94a3b8',
                padding: '0.85rem 1.25rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              ⚙️ Settings & Integrations
            </button>
          </nav>
        </div>
      </header>

      {/* Main Tab Content View */}
      <main style={{ maxWidth: '1380px', margin: '0 auto', padding: '2rem' }}>
        {selectedNetworkId ? (
          <NetworkDetail networkId={selectedNetworkId} onBack={handleBackFromInspect} />
        ) : (
          <>
            {activeTab === 'topology' && <TopologyCanvas />}
            {activeTab === 'networks' && <NetworkList onSelectNetwork={handleSelectNetwork} />}
            {activeTab === 'ipam' && <IPAMDashboard />}
            {activeTab === 'policies' && <PolicyDashboard />}
            {activeTab === 'drift' && <DriftDashboard />}
            {activeTab === 'audit' && <AuditLogList />}
            {activeTab === 'settings' && <SettingsDashboard />}
          </>
        )}
      </main>

      {/* Floating AI Assistant Drawer Component */}
      <AIAssistantDrawer />

      {/* Global Connect Host Modal */}
      <ConnectHostModal
        isOpen={isConnectModalOpen}
        onClose={() => setIsConnectModalOpen(false)}
      />
    </div>
  );
};


const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#090d16',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#38bdf8',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            border: '3px solid rgba(56, 189, 248, 0.2)',
            borderTopColor: '#38bdf8',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginBottom: '1rem',
          }}
        />
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        <div style={{ color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500 }}>
          Initializing Network Control Plane...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return <MainDashboard />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
