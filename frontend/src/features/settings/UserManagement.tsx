import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import {
  Users,
  UserPlus,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Eye,
  Search,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Power,
  RefreshCw,
  Mail,
  User,
  Clock,
  Lock,
} from 'lucide-react';

export interface PlatformUser {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  is_protected?: boolean;
  created_at: string;
  last_login?: string | null;
}

export const UserManagement: React.FC = () => {
  const { user: currentUser, getAuthHeaders } = useAuth();
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'admin' | 'operator' | 'viewer'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'suspended'>('all');

  // Modals & Feedback
  const [isOnboardModalOpen, setIsOnboardModalOpen] = useState<boolean>(false);
  const [deleteTarget, setDeleteTarget] = useState<PlatformUser | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // New User Form State
  const [newUsername, setNewUsername] = useState<string>('');
  const [newEmail, setNewEmail] = useState<string>('');
  const [newRole, setNewRole] = useState<'admin' | 'operator' | 'viewer'>('viewer');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/users', {
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to fetch users' }));
        throw new Error(err.detail || 'Failed to fetch users');
      }
      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      showFeedback('error', err.message || 'Error loading platform users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedback({ type, message });
    setTimeout(() => {
      setFeedback(null);
    }, 4500);
  };

  const handleOnboardUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newEmail.trim()) {
      showFeedback('error', 'Please provide both username and corporate email.');
      return;
    }

    setActionLoading(true);
    try {
      const res = await fetch('/api/v1/auth/users', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          username: newUsername.trim(),
          email: newEmail.trim(),
          role: newRole,
          is_active: true,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to onboard user' }));
        throw new Error(err.detail || 'Failed to onboard user');
      }

      const created = await res.json();
      showFeedback('success', `User '${created.username}' successfully onboarded with role '${created.role}'!`);
      setIsOnboardModalOpen(false);
      setNewUsername('');
      setNewEmail('');
      setNewRole('viewer');
      fetchUsers();
    } catch (err: any) {
      showFeedback('error', err.message || 'Failed to onboard user');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRoleChange = async (username: string, nextRole: 'admin' | 'operator' | 'viewer') => {
    try {
      const res = await fetch(`/api/v1/auth/users/${encodeURIComponent(username)}/role`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ role: nextRole }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to update user role' }));
        throw new Error(err.detail || 'Failed to update user role');
      }

      showFeedback('success', `Role for '${username}' updated to ${nextRole.toUpperCase()}.`);
      fetchUsers();
    } catch (err: any) {
      showFeedback('error', err.message || 'Failed to update role');
    }
  };

  const handleToggleStatus = async (userItem: PlatformUser) => {
    const nextStatus = !userItem.is_active;
    try {
      const res = await fetch(`/api/v1/auth/users/${encodeURIComponent(userItem.username)}/status`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_active: nextStatus }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to toggle account status' }));
        throw new Error(err.detail || 'Failed to toggle account status');
      }

      showFeedback(
        'success',
        `User '${userItem.username}' is now ${nextStatus ? 'ACTIVE' : 'SUSPENDED'}.`
      );
      fetchUsers();
    } catch (err: any) {
      showFeedback('error', err.message || 'Failed to update status');
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    try {
      const res = await fetch(`/api/v1/auth/users/${encodeURIComponent(deleteTarget.username)}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to delete user' }));
        throw new Error(err.detail || 'Failed to delete user');
      }

      showFeedback('success', `User '${deleteTarget.username}' removed from platform.`);
      setDeleteTarget(null);
      fetchUsers();
    } catch (err: any) {
      showFeedback('error', err.message || 'Failed to delete user');
    } finally {
      setActionLoading(false);
    }
  };

  // Filter users
  const filteredUsers = users.filter((u) => {
    const query = searchQuery.toLowerCase();
    const matchesQuery =
      u.username.toLowerCase().includes(query) || u.email.toLowerCase().includes(query);
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && u.is_active) ||
      (statusFilter === 'suspended' && !u.is_active);
    return matchesQuery && matchesRole && matchesStatus;
  });

  const totalUsers = users.length;
  const adminCount = users.filter((u) => u.role === 'admin' && u.is_active).length;
  const operatorCount = users.filter((u) => u.role === 'operator' && u.is_active).length;
  const viewerCount = users.filter((u) => u.role === 'viewer' && u.is_active).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Toast Feedback */}
      {feedback && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.9rem 1.25rem',
            borderRadius: '10px',
            background: feedback.type === 'success' ? '#f0fdf4' : '#fef2f2',
            border: feedback.type === 'success' ? '1px solid #bbf7d0' : '1px solid #fecaca',
            color: feedback.type === 'success' ? '#166534' : '#991b1b',
            fontSize: '0.9rem',
            fontWeight: 600,
            boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
          }}
        >
          {feedback.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem' }}>
        <div
          style={{
            background: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
          }}
        >
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: '#e0f2fe',
              color: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Total Registered</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>{totalUsers}</div>
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
          }}
        >
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: '#f3e8ff',
              color: '#9333ea',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Administrators</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#9333ea' }}>{adminCount}</div>
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
          }}
        >
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldCheck size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Operators</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#d97706' }}>{operatorCount}</div>
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
          }}
        >
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: '#f1f5f9',
              color: '#475569',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Eye size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>Viewers</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#475569' }}>{viewerCount}</div>
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        {/* Title & Action Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              👥 User Access & Role Governance
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.85rem' }}>
              Only onboarded users with an assigned role can sign into the platform via SSO. Uninvited users receive an access denied notice.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <button
              onClick={fetchUsers}
              disabled={loading}
              title="Refresh User Directory"
              style={{
                background: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '0.6rem 0.85rem',
                color: '#475569',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>

            <button
              onClick={() => setIsOnboardModalOpen(true)}
              style={{
                background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '0.6rem 1.25rem',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
              }}
            >
              <UserPlus size={16} />
              + Onboard User
            </button>
          </div>
        </div>

        {/* Root Administrator Immutability Security Callout */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            color: '#334155',
            fontSize: '0.82rem',
            marginBottom: '1.25rem',
          }}
        >
          <Shield size={18} style={{ color: '#7c3aed', flexShrink: 0 }} />
          <div>
            <strong>Root Superadmin Protection:</strong> The default system administrator account (<code style={{ color: '#7c3aed', fontWeight: 600 }}>admin@network-control-plane.local</code>) is protected by system security invariants. Its role is immutable, and other administrators cannot suspend or delete it.
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div
          style={{
            display: 'flex',
            gap: '1rem',
            alignItems: 'center',
            flexWrap: 'wrap',
            padding: '1rem',
            background: '#f8fafc',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            marginBottom: '1.25rem',
          }}
        >
          {/* Search Input */}
          <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by username or corporate email..."
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '0.55rem 0.75rem 0.55rem 2.2rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
                outline: 'none',
                background: '#ffffff',
              }}
            />
          </div>

          {/* Role Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as any)}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
                background: '#ffffff',
                color: '#334155',
              }}
            >
              <option value="all">All Roles</option>
              <option value="admin">Administrators</option>
              <option value="operator">Operators</option>
              <option value="viewer">Viewers</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.85rem',
                background: '#ffffff',
                color: '#334155',
              }}
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="suspended">Suspended Only</option>
            </select>
          </div>
        </div>

        {/* User Directory Table */}
        <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>User Identity</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Assigned Role</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Account Status</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Onboarded Date</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Last Login</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                    Loading user directory...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                    No platform users found matching current filters.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((userItem) => {
                  const isCurrent =
                    userItem.username === currentUser?.user_id ||
                    userItem.email === currentUser?.user_id;
                  const isProtected =
                    Boolean(userItem.is_protected) ||
                    userItem.username.toLowerCase() === 'admin' ||
                    userItem.email.toLowerCase() === 'admin@network-control-plane.local';

                  return (
                    <tr
                      key={userItem.id}
                      style={{
                        borderBottom: '1px solid #f1f5f9',
                        background: isProtected
                          ? '#fbfbfe'
                          : userItem.is_active
                          ? '#ffffff'
                          : '#fafafa',
                      }}
                    >
                      {/* User Column */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div
                            style={{
                              width: '34px',
                              height: '34px',
                              borderRadius: '50%',
                              background:
                                isProtected
                                  ? '#ede9fe'
                                  : userItem.role === 'admin'
                                  ? '#ede9fe'
                                  : userItem.role === 'operator'
                                  ? '#fef3c7'
                                  : '#e0f2fe',
                              color:
                                isProtected
                                  ? '#6d28d9'
                                  : userItem.role === 'admin'
                                  ? '#7c3aed'
                                  : userItem.role === 'operator'
                                  ? '#b45309'
                                  : '#0369a1',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.85rem',
                              flexShrink: 0,
                            }}
                          >
                            {isProtected ? '👑' : userItem.username.substring(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                              {userItem.username}
                              {isProtected && (
                                <span
                                  style={{
                                    fontSize: '0.68rem',
                                    padding: '0.12rem 0.45rem',
                                    background: '#ede9fe',
                                    color: '#6d28d9',
                                    border: '1px solid #ddd6fe',
                                    borderRadius: '9999px',
                                    fontWeight: 700,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '0.2rem',
                                  }}
                                  title="Root Superadmin: account cannot be modified, suspended, or deleted"
                                >
                                  <Lock size={10} />
                                  Root Admin
                                </span>
                              )}
                              {isCurrent && (
                                <span
                                  style={{
                                    fontSize: '0.7rem',
                                    padding: '0.1rem 0.4rem',
                                    background: '#e0f2fe',
                                    color: '#0369a1',
                                    borderRadius: '4px',
                                    fontWeight: 600,
                                  }}
                                >
                                  You
                                </span>
                              )}
                            </div>
                            <div style={{ color: '#64748b', fontSize: '0.78rem' }}>{userItem.email}</div>
                          </div>
                        </div>
                      </td>

                      {/* Role Dropdown */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {isProtected ? (
                          <div
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              padding: '0.35rem 0.65rem',
                              borderRadius: '6px',
                              border: '1px solid #ddd6fe',
                              background: '#faf5ff',
                              color: '#6d28d9',
                              fontWeight: 700,
                              fontSize: '0.8rem',
                              cursor: 'not-allowed',
                            }}
                            title="Root administrator role is immutable and cannot be changed"
                          >
                            <Lock size={12} />
                            <span>Admin</span>
                          </div>
                        ) : (
                          <select
                            value={userItem.role}
                            onChange={(e) =>
                              handleRoleChange(userItem.username, e.target.value as 'admin' | 'operator' | 'viewer')
                            }
                            style={{
                              padding: '0.35rem 0.6rem',
                              borderRadius: '6px',
                              border:
                                userItem.role === 'admin'
                                  ? '1px solid #c084fc'
                                  : userItem.role === 'operator'
                                  ? '1px solid #fcd34d'
                                  : '1px solid #cbd5e1',
                              background:
                                userItem.role === 'admin'
                                  ? '#faf5ff'
                                  : userItem.role === 'operator'
                                  ? '#fffbeb'
                                  : '#f8fafc',
                              color:
                                userItem.role === 'admin'
                                  ? '#7e22ce'
                                  : userItem.role === 'operator'
                                  ? '#b45309'
                                  : '#334155',
                              fontWeight: 600,
                              fontSize: '0.8rem',
                              cursor: 'pointer',
                            }}
                          >
                            <option value="admin">Admin</option>
                            <option value="operator">Operator</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        )}
                      </td>

                      {/* Status Badge */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.55rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            background: userItem.is_active ? '#dcfce7' : '#fee2e2',
                            color: userItem.is_active ? '#15803d' : '#b91c1c',
                          }}
                        >
                          <span
                            style={{
                              width: '6px',
                              height: '6px',
                              borderRadius: '50%',
                              background: userItem.is_active ? '#22c55e' : '#ef4444',
                            }}
                          />
                          {userItem.is_active ? 'ACTIVE' : 'SUSPENDED'}
                        </span>
                      </td>

                      {/* Created At */}
                      <td style={{ padding: '0.85rem 1rem', color: '#64748b', fontSize: '0.8rem' }}>
                        {new Date(userItem.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>

                      {/* Last Login */}
                      <td style={{ padding: '0.85rem 1rem', color: '#64748b', fontSize: '0.8rem' }}>
                        {userItem.last_login
                          ? new Date(userItem.last_login).toLocaleString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : 'Never logged in'}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.5rem', alignItems: 'center' }}>
                          <button
                            type="button"
                            onClick={() => handleToggleStatus(userItem)}
                            disabled={isCurrent || isProtected}
                            title={
                              isProtected
                                ? 'System root administrator cannot be deactivated or suspended'
                                : isCurrent
                                ? 'Cannot suspend your own account'
                                : userItem.is_active
                                ? 'Suspend User Access'
                                : 'Re-activate User Access'
                            }
                            style={{
                              padding: '0.35rem 0.65rem',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              background: '#ffffff',
                              color: isCurrent || isProtected ? '#94a3b8' : userItem.is_active ? '#b91c1c' : '#15803d',
                              cursor: isCurrent || isProtected ? 'not-allowed' : 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              opacity: isCurrent || isProtected ? 0.6 : 1,
                            }}
                          >
                            <Power size={13} />
                            {userItem.is_active ? 'Suspend' : 'Activate'}
                          </button>

                          <button
                            type="button"
                            onClick={() => setDeleteTarget(userItem)}
                            disabled={isCurrent || isProtected}
                            title={
                              isProtected
                                ? 'System root administrator cannot be deleted'
                                : isCurrent
                                ? 'Cannot delete your own account'
                                : 'Delete User'
                            }
                            style={{
                              padding: '0.35rem 0.55rem',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              background: '#ffffff',
                              color: isCurrent || isProtected ? '#94a3b8' : '#ef4444',
                              cursor: isCurrent || isProtected ? 'not-allowed' : 'pointer',
                              opacity: isCurrent || isProtected ? 0.6 : 1,
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal 1: Onboard New User */}
      {isOnboardModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '16px',
              padding: '2rem',
              maxWidth: '480px',
              width: '100%',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
              border: '1px solid #e2e8f0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: '#e0f2fe',
                  color: '#0284c7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <UserPlus size={22} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#0f172a', fontWeight: 700 }}>
                  Onboard Enterprise User
                </h3>
                <p style={{ margin: '0.2rem 0 0 0', color: '#64748b', fontSize: '0.8rem' }}>
                  Pre-provision organizational identity to grant platform access upon SSO sign-in.
                </p>
              </div>
            </div>

            <form onSubmit={handleOnboardUser}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Corporate Email Address <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
                  <input
                    type="email"
                    required
                    value={newEmail}
                    onChange={(e) => {
                      setNewEmail(e.target.value);
                      if (!newUsername) {
                        const prefix = e.target.value.split('@')[0];
                        setNewUsername(prefix);
                      }
                    }}
                    placeholder="e.g. employee@company.com"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '0.6rem 0.85rem 0.6rem 2.2rem',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.85rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Platform Username <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <User size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
                  <input
                    type="text"
                    required
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="e.g. john.doe"
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      padding: '0.6rem 0.85rem 0.6rem 2.2rem',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.85rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Assigned Platform Role <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                  {[
                    { id: 'viewer', title: 'Viewer', desc: 'Read-only inspection' },
                    { id: 'operator', title: 'Operator', desc: 'Mutations & deployment' },
                    { id: 'admin', title: 'Admin', desc: 'Full administration' },
                  ].map((r) => (
                    <div
                      key={r.id}
                      onClick={() => setNewRole(r.id as any)}
                      style={{
                        padding: '0.75rem',
                        borderRadius: '8px',
                        border: newRole === r.id ? '2px solid #0284c7' : '1px solid #cbd5e1',
                        background: newRole === r.id ? '#f0f9ff' : '#ffffff',
                        cursor: 'pointer',
                        textAlign: 'center',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ fontWeight: 700, fontSize: '0.85rem', color: newRole === r.id ? '#0369a1' : '#334155' }}>
                        {r.title}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.2rem' }}>
                        {r.desc}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setIsOnboardModalOpen(false)}
                  style={{
                    padding: '0.6rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    background: '#f8fafc',
                    color: '#475569',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    padding: '0.6rem 1.25rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 2px 6px rgba(2, 132, 199, 0.3)',
                  }}
                >
                  {actionLoading ? 'Onboarding...' : 'Onboard User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Delete User Confirmation */}
      {deleteTarget && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '16px',
              padding: '2rem',
              maxWidth: '440px',
              width: '100%',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
              border: '1px solid #fecaca',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: '#b91c1c' }}>
              <AlertCircle size={28} />
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>Confirm User Removal</h3>
            </div>

            <p style={{ margin: '0 0 1.5rem 0', color: '#475569', fontSize: '0.88rem', lineHeight: 1.5 }}>
              Are you sure you want to remove user <strong>'{deleteTarget.username}'</strong> ({deleteTarget.email})?
              <br /><br />
              They will no longer be authorized to sign into the Network Control Plane.
            </p>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                style={{
                  padding: '0.6rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#f8fafc',
                  color: '#475569',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleDeleteUser}
                disabled={actionLoading}
                style={{
                  padding: '0.6rem 1.25rem',
                  borderRadius: '8px',
                  border: 'none',
                  background: '#ef4444',
                  color: '#ffffff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: actionLoading ? 'not-allowed' : 'pointer',
                }}
              >
                {actionLoading ? 'Deleting...' : 'Remove User'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
