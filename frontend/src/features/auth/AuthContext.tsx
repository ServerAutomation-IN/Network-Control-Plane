import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface AuthUser {
  user_id: string;
  role: 'admin' | 'operator' | 'viewer';
  email?: string;
  provider?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  role: 'admin' | 'operator' | 'viewer';
  isAuthenticated: boolean;
  loading: boolean;
  setupRequired: boolean;
  authError: string | null;
  clearAuthError: () => void;
  checkSetupStatus: () => Promise<boolean>;
  login: (username: string, password: string) => Promise<void>;
  setupAdmin: (username: string, email: string, password: string) => Promise<void>;
  directLogin: (username: string, role?: string) => Promise<void>;
  logout: () => void;
  getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'ncp_auth_token';
const USER_KEY = 'ncp_auth_user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem(USER_KEY);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [setupRequired, setSetupRequired] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const clearAuthError = () => setAuthError(null);

  const checkSetupStatus = async (): Promise<boolean> => {
    try {
      const res = await fetch('/api/v1/auth/setup-status');
      if (res.ok) {
        const data = await res.json();
        setSetupRequired(Boolean(data.setup_required));
        return Boolean(data.setup_required);
      }
    } catch (err) {
      console.warn('Failed to fetch setup status:', err);
    }
    return false;
  };

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);

      // Check if arriving from an OAuth2 / OIDC SSO redirect with an authorization code
      const params = new URLSearchParams(window.location.search);
      const authCode = params.get('code');
      const ssoProvider = params.get('provider') || 'okta';

      if (authCode) {
        try {
          const redirectUri = `${window.location.origin}${window.location.pathname}`;
          const res = await fetch(`/api/v1/auth/callback/${ssoProvider}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: authCode, redirect_uri: redirectUri }),
          });

          if (res.ok) {
            const data = await res.json();
            const ssoUser: AuthUser = {
              user_id: data.user_id,
              role: (data.role || 'admin') as 'admin' | 'operator' | 'viewer',
              provider: data.provider || ssoProvider,
            };
            setToken(data.access_token);
            setUser(ssoUser);
            localStorage.setItem(TOKEN_KEY, data.access_token);
            localStorage.setItem(USER_KEY, JSON.stringify(ssoUser));
            setSetupRequired(false);
            setAuthError(null);
            window.history.replaceState({}, document.title, window.location.pathname);
            setLoading(false);
            return;
          } else {
            const errData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
            setAuthError(
              errData.detail ||
                'You are not authorized to access this application. Please contact your platform administrator.'
            );
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } catch (err: any) {
          console.error('Failed to exchange SSO authorization code:', err);
          setAuthError(err.message || 'Failed to complete SSO authentication.');
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }

      const isRequired = await checkSetupStatus();

      if (!isRequired && token) {
        try {
          const res = await fetch('/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          if (res.ok) {
            const data = await res.json();
            const validatedUser: AuthUser = {
              user_id: data.user_id,
              role: (data.role || 'admin') as 'admin' | 'operator' | 'viewer',
            };
            setUser(validatedUser);
            localStorage.setItem(USER_KEY, JSON.stringify(validatedUser));
          } else {
            // Invalid token
            logout();
          }
        } catch {
          // Keep local session if server temporarily offline
        }
      } else if (isRequired) {
        // Clear any stale local user if fresh setup is required
        logout();
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string): Promise<void> => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(err.detail || 'Invalid username or password');
    }

    const data = await res.json();
    const newUser: AuthUser = {
      user_id: data.user_id,
      role: (data.role || 'admin') as 'admin' | 'operator' | 'viewer',
      provider: data.provider || 'local',
    };

    setToken(data.access_token);
    setUser(newUser);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setSetupRequired(false);
  };

  const setupAdmin = async (username: string, email: string, password: string): Promise<void> => {
    const res = await fetch('/api/v1/auth/setup-admin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Setup failed' }));
      throw new Error(err.detail || 'Failed to setup initial administrator');
    }

    const data = await res.json();
    const newUser: AuthUser = {
      user_id: data.user_id,
      role: 'admin',
      email: data.email,
      provider: 'local',
    };

    setToken(data.access_token);
    setUser(newUser);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setSetupRequired(false);
  };

  const directLogin = async (username: string, role: string = 'admin'): Promise<void> => {
    const res = await fetch('/api/v1/auth/login/direct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password: 'direct-login-token',
        requested_role: role,
      }),
    });

    if (!res.ok) {
      throw new Error('Direct login failed');
    }

    const data = await res.json();
    const newUser: AuthUser = {
      user_id: data.user_id,
      role: (data.role || 'admin') as 'admin' | 'operator' | 'viewer',
      provider: 'direct',
    };

    setToken(data.access_token);
    setUser(newUser);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const getAuthHeaders = (): Record<string, string> => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (user) {
      headers['X-User-Role'] = user.role;
      headers['X-User-Id'] = user.user_id;
    }
    return headers;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || 'admin',
        isAuthenticated: Boolean(token && user),
        loading,
        setupRequired,
        authError,
        clearAuthError,
        checkSetupStatus,
        login,
        setupAdmin,
        directLogin,
        logout,
        getAuthHeaders,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
