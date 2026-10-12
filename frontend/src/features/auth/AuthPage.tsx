import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import { Shield, Lock, User, Key, ArrowRight, CheckCircle2, AlertCircle, Sparkles, Server } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { setupRequired, login, setupAdmin, directLogin, authError, clearAuthError } = useAuth();
  const [isSetupMode, setIsSetupMode] = useState<boolean>(setupRequired);

  // Form states
  const [username, setUsername] = useState<string>('admin');
  const [email, setEmail] = useState<string>('admin@network-control-plane.local');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [authTab, setAuthTab] = useState<'credentials' | 'sso'>('credentials');

  // Status feedback
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleAdminSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match. Please verify both fields.');
      return;
    }

    setSubmitting(true);
    try {
      await setupAdmin(username, email, password);
      setSuccessMsg('Administrator account initialized successfully!');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to complete initial administrator setup');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSubmitting(true);

    try {
      await login(username, password);
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid credentials. Please verify your username and password.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickDemoLogin = async (demoRole: 'admin' | 'operator' | 'viewer') => {
    setErrorMsg(null);
    setSubmitting(true);
    try {
      await directLogin(`demo-${demoRole}`, demoRole);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to initiate quick demo session');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSsoRedirect = async (providerId: string) => {
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      const res = await fetch(`/api/v1/auth/login/${providerId}?redirect_uri=${encodeURIComponent(redirectUri)}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to initiate SSO login' }));
        throw new Error(err.detail || 'Failed to initiate SSO login');
      }
      const data = await res.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch (err: any) {
      setErrorMsg(`${err.message} (Tip: If testing in an offline or lab environment without a live IdP, use the Demo shortcuts below)`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'radial-gradient(ellipse at 50% 20%, #1e1b4b 0%, #090d16 65%, #020617 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem 1rem',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        color: '#f8fafc',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative ambient background glows */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: '15%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '-10%',
          right: '15%',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.14) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Glass Card */}
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '24px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)',
          padding: '2.5rem',
          zIndex: 1,
          position: 'relative',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
              boxShadow: '0 8px 16px -4px rgba(2, 132, 199, 0.4)',
              marginBottom: '1rem',
            }}
          >
            <Shield size={28} color="#ffffff" />
          </div>
          <h1
            style={{
              margin: '0 0 0.5rem 0',
              fontSize: '1.75rem',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              background: 'linear-gradient(135deg, #38bdf8 0%, #c084fc 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Network Control Plane
          </h1>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>
            Visualize. Manage. Validate. Govern. Automate Workload Networking.
          </p>
          <div style={{ marginTop: '0.5rem' }}>
            <span
              style={{
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                color: '#38bdf8',
                padding: '0.2rem 0.6rem',
                borderRadius: '12px',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
            >
              v1.0.0-GA
            </span>
          </div>
        </div>

        {/* Alert Notifications */}
        {errorMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '12px',
              padding: '0.85rem 1rem',
              marginBottom: '1.5rem',
              color: '#fca5a5',
              fontSize: '0.85rem',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              background: 'rgba(34, 197, 94, 0.12)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              borderRadius: '12px',
              padding: '0.85rem 1rem',
              marginBottom: '1.5rem',
              color: '#86efac',
              fontSize: '0.85rem',
            }}
          >
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* State 1: Uninvited or Suspended Access Denied */}
        {authError ? (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: '16px',
              padding: '1.75rem 1.5rem',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1.25rem auto',
                color: '#f87171',
              }}
            >
              <Lock size={26} />
            </div>

            <h2
              style={{
                margin: '0 0 0.5rem 0',
                fontSize: '1.3rem',
                fontWeight: 700,
                color: '#fca5a5',
              }}
            >
              Access Denied
            </h2>

            <div
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '10px',
                padding: '0.85rem 1rem',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '0.92rem',
                marginBottom: '1rem',
                lineHeight: 1.5,
              }}
            >
              {authError}
            </div>

            <p
              style={{
                margin: '0 0 1.5rem 0',
                fontSize: '0.85rem',
                color: '#94a3b8',
                lineHeight: 1.6,
              }}
            >
              Your identity was verified by your organization's Identity Provider, but your account has not been onboarded or assigned an access role in the Network Control Plane.
              <br /><br />
              Please contact your designated platform administrator to have your account onboarded and assigned a role.
            </p>

            <button
              type="button"
              onClick={clearAuthError}
              style={{
                width: '100%',
                padding: '0.75rem 1.25rem',
                background: 'linear-gradient(135deg, #334155 0%, #1e293b 100%)',
                border: '1px solid #475569',
                borderRadius: '10px',
                color: '#f8fafc',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                transition: 'all 0.15s ease',
              }}
            >
              ← Return to Sign In
            </button>
          </div>
        ) : isSetupMode ? (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1rem',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '12px',
                marginBottom: '1.5rem',
              }}
            >
              <Sparkles size={18} color="#a5b4fc" />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e0e7ff' }}>
                  First-Time Platform Initialization
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Setup the primary superuser administrator account to unlock the control plane.
                </div>
              </div>
            </div>

            <form onSubmit={handleAdminSetup}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Administrator Username
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '0.65rem 1rem 0.65rem 2.5rem',
                      background: 'rgba(30, 41, 59, 0.8)',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Administrator Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@company.internal"
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    padding: '0.65rem 1rem',
                    background: 'rgba(30, 41, 59, 0.8)',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '0.9rem',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Master Password (min. 8 characters)
                </label>
                <div style={{ position: 'relative' }}>
                  <Key size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '0.65rem 1rem 0.65rem 2.5rem',
                      background: 'rgba(30, 41, 59, 0.8)',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Confirm Master Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '0.65rem 1rem 0.65rem 2.5rem',
                      background: 'rgba(30, 41, 59, 0.8)',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
                  border: 'none',
                  borderRadius: '12px',
                  color: '#ffffff',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
                  transition: 'opacity 0.2s',
                  opacity: submitting ? 0.7 : 1,
                }}
              >
                {submitting ? 'Initializing Platform...' : 'Initialize & Sign In'}
                <ArrowRight size={18} />
              </button>
            </form>

            {!setupRequired && (
              <div style={{ textAlign: 'center', marginTop: '1.25rem' }}>
                <button
                  type="button"
                  onClick={() => setIsSetupMode(false)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Already have an account? Sign in here
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Mode 2: User Sign In */
          <div>
            {/* Auth Tab Selector */}
            <div
              style={{
                display: 'flex',
                background: 'rgba(30, 41, 59, 0.6)',
                borderRadius: '12px',
                padding: '0.25rem',
                marginBottom: '1.5rem',
                border: '1px solid #334155',
              }}
            >
              <button
                type="button"
                onClick={() => setAuthTab('credentials')}
                style={{
                  flex: 1,
                  padding: '0.55rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: authTab === 'credentials' ? '#1e293b' : 'transparent',
                  color: authTab === 'credentials' ? '#38bdf8' : '#94a3b8',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                Direct Credentials
              </button>
              <button
                type="button"
                onClick={() => setAuthTab('sso')}
                style={{
                  flex: 1,
                  padding: '0.55rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: authTab === 'sso' ? '#1e293b' : 'transparent',
                  color: authTab === 'sso' ? '#38bdf8' : '#94a3b8',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                Enterprise SSO
              </button>
            </div>

            {authTab === 'credentials' ? (
              <form onSubmit={handleLogin}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                    Username or Email
                  </label>
                  <div style={{ position: 'relative' }}>
                    <User size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
                    <input
                      type="text"
                      required
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Username or email"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '0.65rem 1rem 0.65rem 2.5rem',
                        background: 'rgba(30, 41, 59, 0.8)',
                        border: '1px solid #334155',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '0.9rem',
                        outline: 'none',
                      }}
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                    Password
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '0.65rem 1rem 0.65rem 2.5rem',
                        background: 'rgba(30, 41, 59, 0.8)',
                        border: '1px solid #334155',
                        borderRadius: '10px',
                        color: '#ffffff',
                        fontSize: '0.9rem',
                        outline: 'none',
                      }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    width: '100%',
                    padding: '0.85rem',
                    background: 'linear-gradient(135deg, #0284c7 0%, #6366f1 100%)',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
                    opacity: submitting ? 0.7 : 1,
                  }}
                >
                  {submitting ? 'Authenticating...' : 'Sign In'}
                  <ArrowRight size={18} />
                </button>
              </form>
            ) : (
              /* SSO Options */
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <p style={{ margin: '0 0 0.5rem 0', color: '#94a3b8', fontSize: '0.8rem', textAlign: 'center' }}>
                  Authenticate via your organization's configured Identity Provider:
                </p>
                <button
                  type="button"
                  onClick={() => handleSsoRedirect('keycloak')}
                  disabled={submitting}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <Server size={16} color="#38bdf8" />
                  Keycloak OIDC Single Sign-On
                </button>
                <button
                  type="button"
                  onClick={() => handleSsoRedirect('okta')}
                  disabled={submitting}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <Shield size={16} color="#818cf8" />
                  Okta SSO Gateway
                </button>
                <button
                  type="button"
                  onClick={() => handleSsoRedirect('azure-ad')}
                  disabled={submitting}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#e2e8f0',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.6rem',
                  }}
                >
                  <Key size={16} color="#34d399" />
                  Microsoft Entra ID (Azure AD)
                </button>
              </div>
            )}

            {/* Quick Demo Lab Access */}
            <div
              style={{
                marginTop: '1.75rem',
                paddingTop: '1.25rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.6rem' }}>
                LOCAL LAB & EVALUATION QUICK SHORTCUTS
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={() => handleQuickDemoLogin('admin')}
                  style={{
                    background: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    color: '#38bdf8',
                    padding: '0.35rem 0.65rem',
                    borderRadius: '8px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Demo Admin
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickDemoLogin('operator')}
                  style={{
                    background: 'rgba(251, 191, 36, 0.08)',
                    border: '1px solid rgba(251, 191, 36, 0.2)',
                    color: '#fbbf24',
                    padding: '0.35rem 0.65rem',
                    borderRadius: '8px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Demo Operator
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickDemoLogin('viewer')}
                  style={{
                    background: 'rgba(148, 163, 184, 0.08)',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                    color: '#94a3b8',
                    padding: '0.35rem 0.65rem',
                    borderRadius: '8px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Demo Viewer
                </button>
              </div>

              {/* Toggle to Setup mode if needed */}
              <div style={{ marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setIsSetupMode(true)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#64748b',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                  }}
                >
                  Need to setup a new Administrator account?
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Branding */}
      <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.75rem', color: '#64748b' }}>
        Enterprise Zero-Trust Networking • Built for Container and Multi-Cloud Workloads
      </div>
    </div>
  );
};
