import React, { useState, useEffect } from 'react';
import {
  Server,
  Terminal,
  Copy,
  Check,
  X,
  Clock,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  Monitor,
} from 'lucide-react';

interface BootstrapTokenData {
  token: string;
  expires_in: number;
  expires_at: string;
  control_plane_url: string;
  commands: {
    linux: string;
    windows: string;
    docker: string;
  };
}

interface EnrolledHost {
  id: string;
  name: string;
  provider_type: string;
  status: string;
  os?: string;
  architecture?: string;
  endpoint: string;
}

interface ConnectHostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onHostConnected?: (hostId: string) => void;
}

type TabOS = 'linux' | 'windows' | 'docker';

export const ConnectHostModal: React.FC<ConnectHostModalProps> = ({
  isOpen,
  onClose,
  onHostConnected,
}) => {
  const [activeOS, setActiveOS] = useState<TabOS>('linux');
  const [tokenData, setTokenData] = useState<BootstrapTokenData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);
  const [status, setStatus] = useState<'WAITING' | 'ONLINE' | 'EXPIRED'>('WAITING');
  const [enrolledHost, setEnrolledHost] = useState<EnrolledHost | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(900);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Request new bootstrap token from backend
  const fetchToken = async () => {
    setLoading(true);
    setErrorMessage(null);
    setStatus('WAITING');
    setEnrolledHost(null);
    try {
      const res = await fetch('/api/v1/hosts/bootstrap-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Role': 'admin',
        },
        body: JSON.stringify({ environment: 'production' }),
      });
      if (!res.ok) {
        throw new Error(`Failed to generate bootstrap token (HTTP ${res.status})`);
      }
      const data: BootstrapTokenData = await res.json();
      setTokenData(data);
      setTimeLeft(data.expires_in || 900);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to issue bootstrap token.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchToken();
    }
  }, [isOpen]);

  // Countdown timer for 15-minute expiration
  useEffect(() => {
    if (!isOpen || status === 'ONLINE' || status === 'EXPIRED') return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setStatus('EXPIRED');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen, status]);

  // Poll bootstrap status every 3 seconds while waiting
  useEffect(() => {
    if (!isOpen || !tokenData || status !== 'WAITING') return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/hosts/bootstrap-status/${tokenData.token}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.status === 'ONLINE' && data.host) {
          setStatus('ONLINE');
          setEnrolledHost(data.host);
          if (onHostConnected) {
            onHostConnected(data.host.id);
          }
        } else if (data.status === 'EXPIRED') {
          setStatus('EXPIRED');
        }
      } catch (err) {
        // Poll failure is tolerated
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [isOpen, tokenData, status, onHostConnected]);

  const handleCopy = () => {
    if (!tokenData) return;
    const cmd = tokenData.commands[activeOS];
    navigator.clipboard.writeText(cmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
      }}
    >
      <div
        style={{
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '680px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          color: '#f8fafc',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(to right, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <Server size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Connect Infrastructure Host
              </h2>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
                One-Click Onboarding Wizard — Network Control Plane
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '0.25rem',
              borderRadius: '6px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {errorMessage && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                color: '#f87171',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <AlertTriangle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Ephemeral Token Header Info */}
          <div
            style={{
              background: '#1e293b',
              borderRadius: '10px',
              padding: '0.75rem 1rem',
              border: '1px solid #334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={18} style={{ color: '#38bdf8' }} />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>
                Ephemeral Bootstrap Token:
              </span>
              <code style={{ background: '#090d16', padding: '0.15rem 0.4rem', borderRadius: '4px', fontSize: '0.8rem', color: '#38bdf8' }}>
                {tokenData ? `${tokenData.token.substring(0, 16)}...` : 'Generating...'}
              </code>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: status === 'EXPIRED' ? '#f87171' : '#fbbf24' }}>
              <Clock size={14} />
              <span>{status === 'EXPIRED' ? 'Token Expired' : `Expires in ${formatTime(timeLeft)}`}</span>
            </div>
          </div>

          {/* OS Environment Selector Tabs */}
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '0.5rem' }}>
              1. Select Host OS / Environment:
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
              <button
                type="button"
                onClick={() => setActiveOS('linux')}
                style={{
                  padding: '0.65rem',
                  borderRadius: '8px',
                  border: activeOS === 'linux' ? '2px solid #38bdf8' : '1px solid #334155',
                  background: activeOS === 'linux' ? 'rgba(56, 189, 248, 0.12)' : '#1e293b',
                  color: activeOS === 'linux' ? '#38bdf8' : '#cbd5e1',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <Terminal size={16} />
                Linux (Bash/systemd)
              </button>

              <button
                type="button"
                onClick={() => setActiveOS('windows')}
                style={{
                  padding: '0.65rem',
                  borderRadius: '8px',
                  border: activeOS === 'windows' ? '2px solid #38bdf8' : '1px solid #334155',
                  background: activeOS === 'windows' ? 'rgba(56, 189, 248, 0.12)' : '#1e293b',
                  color: activeOS === 'windows' ? '#38bdf8' : '#cbd5e1',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <Monitor size={16} />
                Windows Server (PowerShell)
              </button>

              <button
                type="button"
                onClick={() => setActiveOS('docker')}
                style={{
                  padding: '0.65rem',
                  borderRadius: '8px',
                  border: activeOS === 'docker' ? '2px solid #38bdf8' : '1px solid #334155',
                  background: activeOS === 'docker' ? 'rgba(56, 189, 248, 0.12)' : '#1e293b',
                  color: activeOS === 'docker' ? '#38bdf8' : '#cbd5e1',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <Server size={16} />
                Docker Container
              </button>
            </div>
          </div>

          {/* Installer Command Box */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>
                2. Run this automated command in your host terminal:
              </label>
              <button
                type="button"
                onClick={handleCopy}
                disabled={loading || !tokenData}
                style={{
                  background: copied ? 'rgba(34, 197, 94, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                  border: copied ? '1px solid #22c55e' : '1px solid #38bdf8',
                  color: copied ? '#4ade80' : '#38bdf8',
                  padding: '0.3rem 0.65rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                }}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy Command'}
              </button>
            </div>

            <div
              style={{
                background: '#090d16',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                padding: '1rem',
                position: 'relative',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                lineHeight: 1.5,
                color: '#38bdf8',
                wordBreak: 'break-all',
                minHeight: '60px',
              }}
            >
              {loading ? (
                <span style={{ color: '#64748b' }}>Generating secure bootstrap command...</span>
              ) : tokenData ? (
                tokenData.commands[activeOS]
              ) : (
                <span style={{ color: '#ef4444' }}>Error loading command. Please regenerate.</span>
              )}
            </div>
          </div>

          {/* Connection Status Card */}
          <div
            style={{
              padding: '1.25rem',
              borderRadius: '10px',
              border:
                status === 'ONLINE'
                  ? '1px solid #22c55e'
                  : status === 'EXPIRED'
                  ? '1px solid #ef4444'
                  : '1px solid #334155',
              background:
                status === 'ONLINE'
                  ? 'rgba(34, 197, 94, 0.08)'
                  : status === 'EXPIRED'
                  ? 'rgba(239, 68, 68, 0.08)'
                  : '#1e293b',
            }}
          >
            {status === 'WAITING' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <RefreshCw
                  size={20}
                  className="animate-spin"
                  style={{ color: '#38bdf8', animation: 'spin 2s linear infinite' }}
                />
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
                    Waiting for host heartbeat... ⏳
                  </h4>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                    Paste and execute the command above on your server. Once the agent starts, connection will be detected automatically.
                  </p>
                </div>
              </div>
            )}

            {status === 'ONLINE' && enrolledHost && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#4ade80', marginBottom: '0.5rem' }}>
                  <Check size={20} />
                  <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>
                    Host Connected Successfully! 🎉
                  </h4>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '0.5rem',
                    background: '#090d16',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    marginTop: '0.5rem',
                  }}
                >
                  <div>
                    <span style={{ color: '#64748b' }}>Host ID: </span>
                    <strong style={{ color: '#f8fafc' }}>{enrolledHost.id}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Hostname: </span>
                    <strong style={{ color: '#f8fafc' }}>{enrolledHost.name}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Runtime: </span>
                    <strong style={{ color: '#38bdf8' }}>{enrolledHost.provider_type}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Status: </span>
                    <strong style={{ color: '#4ade80' }}>ONLINE</strong>
                  </div>
                </div>
              </div>
            )}

            {status === 'EXPIRED' && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171' }}>
                  <AlertTriangle size={18} />
                  <span>This bootstrap token has expired.</span>
                </div>
                <button
                  type="button"
                  onClick={fetchToken}
                  style={{
                    background: '#0284c7',
                    border: 'none',
                    color: '#ffffff',
                    padding: '0.4rem 0.75rem',
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Generate New Token
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            background: '#0f172a',
          }}
        >
          {status === 'ONLINE' ? (
            <button
              onClick={onClose}
              style={{
                background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '0.55rem 1.25rem',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              Done <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={onClose}
              style={{
                background: '#1e293b',
                border: '1px solid #334155',
                color: '#cbd5e1',
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
