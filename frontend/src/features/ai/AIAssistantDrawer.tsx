import React, { useState, useEffect } from 'react';

export interface AIActionProposal {
  id: string;
  action_type: string;
  target_resource: string;
  host_id: string;
  parameters: Record<string, any>;
  risk_level: string;
  reason: string;
}

export interface AIQueryResponse {
  provider_used: string;
  prompt: string;
  reasoning: string;
  query_results?: Record<string, any>;
  reachability_status?: string;
  proposal_id?: string;
  proposed_actions: AIActionProposal[];
}

export interface AIProposalJob {
  id: string;
  user_prompt: string;
  diagnostic_type: string;
  reasoning_summary: string;
  proposed_actions: AIActionProposal[];
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'EXECUTED' | 'REJECTED';
  approved_by?: string;
  execution_result?: Record<string, any>;
  created_at: string;
}

export const AIAssistantDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [promptInput, setPromptInput] = useState<string>('');
  const [provider, setProvider] = useState<string>('mock');
  const [loading, setLoading] = useState<boolean>(false);
  const [chatHistory, setChatHistory] = useState<AIQueryResponse[]>([]);
  const [activeProposal, setActiveProposal] = useState<AIProposalJob | null>(null);
  const [userRole, setUserRole] = useState<'admin' | 'operator' | 'viewer'>('admin');

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': userRole,
    'X-User-Id': `user-${userRole}`,
  });

  const parseErrorMessage = (errJson: any, defaultMsg: string): string => {
    if (!errJson || !errJson.detail) return defaultMsg;
    if (typeof errJson.detail === 'string') return errJson.detail;
    if (Array.isArray(errJson.detail)) {
      return errJson.detail.map((d: any) => d.msg || d.detail || JSON.stringify(d)).join('; ');
    }
    if (typeof errJson.detail === 'object') return JSON.stringify(errJson.detail);
    return String(errJson.detail);
  };

  const renderFormattedContent = (text: string) => {
    if (!text) return null;
    const lines = text.split('\n');

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {lines.map((line, idx) => {
          // Skip table separator row like |---|---|
          if (line.trim().startsWith('|') && (line.includes('---') || line.includes(':---'))) {
            return null;
          }

          // Handle Markdown Table Rows
          if (line.trim().startsWith('|')) {
            const cells = line.split('|').map((c) => c.trim()).filter(Boolean);
            if (cells.length > 0) {
              const isHeader = idx === 0 || (lines[idx - 1] && lines[idx - 1].includes('---')) || cells.some((c) => c.toLowerCase().includes('name') || c.toLowerCase().includes('driver') || c === '#');
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    gap: '0.5rem',
                    background: isHeader ? '#1e293b' : idx % 2 === 0 ? '#f8fafc' : '#ffffff',
                    color: isHeader ? '#38bdf8' : '#334155',
                    padding: '0.35rem 0.65rem',
                    borderRadius: '4px',
                    fontSize: '0.78rem',
                    fontFamily: 'monospace',
                    border: '1px solid #cbd5e1',
                    overflowX: 'auto',
                  }}
                >
                  {cells.map((cell, cIdx) => (
                    <span key={cIdx} style={{ flex: 1, minWidth: '60px', fontWeight: isHeader ? 700 : 400, whiteSpace: 'nowrap' }}>
                      {cell.replace(/\*\*/g, '')}
                    </span>
                  ))}
                </div>
              );
            }
          }

          // Clean bold and backticks formatting for standard prose lines
          const formatted = line.replace(/\*\*(.*?)\*\*/g, '$1').replace(/`(.*?)`/g, '$1');

          return (
            <div key={idx} style={{ minHeight: line.trim() ? 'auto' : '0.4rem', color: '#0f172a', lineHeight: '1.45' }}>
              {formatted}
            </div>
          );
        })}
      </div>
    );
  };

  const handleSendQuery = async (queryText?: string) => {
    const text = queryText || promptInput;
    if (!text.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('/api/v1/ai/query', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ prompt: text, provider }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(parseErrorMessage(errJson, 'AI Query failed'));
      }

      const data: AIQueryResponse = await res.json();
      setChatHistory((prev) => [...prev, data]);
      setPromptInput('');

      if (data.proposal_id) {
        // Fetch proposal job
        const propRes = await fetch(`/api/v1/ai/proposals/${data.proposal_id}`, { headers: getHeaders() });
        if (propRes.ok) {
          setActiveProposal(await propRes.json());
        }
      }
    } catch (err: any) {
      alert(`AI Query Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!activeProposal) return;
    try {
      const res = await fetch(`/api/v1/ai/proposals/${activeProposal.id}/approve`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(parseErrorMessage(errJson, 'Approval failed'));
      }
      setActiveProposal(await res.json());
    } catch (err: any) {
      alert(`Approval Error: ${err.message}`);
    }
  };

  const handleExecuteProposal = async () => {
    if (!activeProposal) return;
    if (!window.confirm('Execute AI remediation proposal actions?')) return;

    try {
      const res = await fetch(`/api/v1/ai/proposals/${activeProposal.id}/execute`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(parseErrorMessage(errJson, 'Execution failed'));
      }
      setActiveProposal(await res.json());
    } catch (err: any) {
      alert(`Execution Error: ${err.message}`);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)',
          color: '#ffffff',
          border: 'none',
          borderRadius: '30px',
          padding: '0.85rem 1.4rem',
          fontSize: '0.95rem',
          fontWeight: 700,
          cursor: 'pointer',
          boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.4)',
          zIndex: 999,
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
        }}
      >
        <span>🤖</span> Network AI Assistant
      </button>

      {/* Slide-over Drawer Panel */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            right: 0,
            width: '100%',
            maxWidth: '540px',
            height: '100vh',
            background: '#ffffff',
            borderLeft: '1px solid #e2e8f0',
            boxShadow: '-10px 0 30px rgba(0,0,0,0.15)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Drawer Header */}
          <div style={{ padding: '1.25rem 1.5rem', background: '#0f172a', color: '#ffffff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>
                🤖 Network Control Plane AI Assistant
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', color: '#94a3b8', fontSize: '0.8rem' }}>
                Natural Language Infrastructure Query & HITL Governed Diagnostics
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.4rem', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          {/* Controls Bar */}
          <div style={{ padding: '0.75rem 1.25rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '0.75rem', alignItems: 'center', fontSize: '0.85rem' }}>
            <label style={{ fontWeight: 600, color: '#475569' }}>Provider:</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              style={{ border: '1px solid #cbd5e1', borderRadius: '6px', padding: '0.3rem 0.6rem', fontSize: '0.85rem', fontWeight: 600 }}
            >
              <option value="mock">Mock LLM (Deterministic)</option>
              <option value="ollama">Ollama (Local LLM)</option>
              <option value="openai">OpenAI</option>
              <option value="azure">Azure OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          {/* Quick Prompt Chips */}
          <div style={{ padding: '0.75rem 1.25rem', background: '#ffffff', borderBottom: '1px solid #f1f5f9', display: 'flex', gap: '0.5rem', overflowX: 'auto' }}>
            <button
              onClick={() => handleSendQuery('Diagnose why container langfuse-worker cannot reach postgres')}
              style={{ background: '#e0f2fe', color: '#0369a1', border: 'none', borderRadius: '16px', padding: '0.3rem 0.75rem', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              🩺 Reachability Diagnostic
            </button>
            <button
              onClick={() => handleSendQuery('Show production networks and utilization')}
              style={{ background: '#fef3c7', color: '#92400e', border: 'none', borderRadius: '16px', padding: '0.3rem 0.75rem', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              📊 Subnet Utilization
            </button>
          </div>

          {/* Chat Messages Feed */}
          <div style={{ flex: 1, padding: '1.25rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', background: '#f8fafc' }}>
            {chatHistory.length === 0 ? (
              <div style={{ padding: '3rem 1rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
                Ask a natural language query or diagnose inter-container reachability!
              </div>
            ) : (
              chatHistory.map((msg, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {/* User Question */}
                  <div style={{ alignSelf: 'flex-end', background: '#2563eb', color: '#ffffff', padding: '0.75rem 1rem', borderRadius: '12px 12px 0 12px', fontSize: '0.875rem', maxWidth: '85%' }}>
                    {msg.prompt}
                  </div>

                  {/* AI Response Card */}
                  <div style={{ alignSelf: 'flex-start', background: '#ffffff', border: '1px solid #e2e8f0', padding: '1rem', borderRadius: '12px 12px 12px 0', fontSize: '0.875rem', maxWidth: '90%', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 700, marginBottom: '0.4rem' }}>
                      {msg.provider_used}
                    </div>
                    {msg.reachability_status && (
                      <span style={{ background: msg.reachability_status === 'REACHABLE' ? '#dcfce7' : '#fee2e2', color: msg.reachability_status === 'REACHABLE' ? '#166534' : '#991b1b', padding: '0.2rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700, display: 'inline-block', marginBottom: '0.5rem' }}>
                        {msg.reachability_status}
                      </span>
                    )}
                    <div style={{ color: '#0f172a', lineHeight: '1.5' }}>
                      {renderFormattedContent(
                        msg.reasoning && msg.reasoning.trim()
                          ? msg.reasoning
                          : msg.query_results
                          ? `Inventory Summary:\n• Hosts: ${msg.query_results.total_hosts}\n• Active Networks: ${msg.query_results.total_networks}`
                          : 'No reasoning output returned from model.'
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* HITL Proposal Approval Banner (if generated) */}
          {activeProposal && (
            <div style={{ padding: '1rem 1.25rem', background: '#fffbe8', borderTop: '1px solid #fde68a' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#92400e', marginBottom: '0.4rem' }}>
                🛡️ Human-in-the-Loop Remediation Proposal (Status: {activeProposal.status})
              </div>
              {activeProposal.proposed_actions.map((act) => (
                <div key={act.id} style={{ fontSize: '0.8rem', color: '#475569', marginBottom: '0.5rem' }}>
                  👉 {act.reason} (Risk: <strong>{act.risk_level}</strong>)
                </div>
              ))}

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                {activeProposal.status === 'PENDING_APPROVAL' && (
                  <button
                    onClick={handleApproveProposal}
                    style={{ flex: 1, background: '#16a34a', color: '#ffffff', border: 'none', padding: '0.5rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                    👍 Approve Proposal
                  </button>
                )}
                {activeProposal.status === 'APPROVED' && (
                  <button
                    onClick={handleExecuteProposal}
                    style={{ flex: 1, background: '#d97706', color: '#ffffff', border: 'none', padding: '0.5rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                    🚀 Execute Approved Actions
                  </button>
                )}
                {activeProposal.status === 'EXECUTED' && (
                  <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 700 }}>
                    ✅ Proposal Successfully Executed!
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Input Prompt Box */}
          <div style={{ padding: '1rem 1.25rem', background: '#ffffff', borderTop: '1px solid #e2e8f0', display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
              placeholder="Ask AI or diagnose network reachability..."
              style={{ flex: 1, padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.875rem' }}
            />
            <button
              onClick={() => handleSendQuery()}
              disabled={loading}
              style={{ background: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '8px', padding: '0.65rem 1.25rem', fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}
            >
              {loading ? 'Thinking...' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </>
  );
};
