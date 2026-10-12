import React, { useState, useEffect } from 'react';

export interface BackgroundTask {
  id: string;
  task_type: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  worker_id: string;
  payload: Record<string, any>;
  result?: Record<string, any>;
  error_log?: string;
  retry_count: number;
  max_retries: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface QueueMetrics {
  active_workers: number;
  queued_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  avg_latency_ms: number;
}

export const BackgroundQueueDashboard: React.FC = () => {
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [metrics, setMetrics] = useState<QueueMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedTaskLog, setSelectedTaskLog] = useState<BackgroundTask | null>(null);

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'X-User-Role': 'admin',
    'X-User-Id': 'admin-user',
  });

  const fetchQueueData = async () => {
    setLoading(true);
    try {
      const [tasksRes, metricsRes] = await Promise.all([
        fetch('/api/v1/tasks/queue', { headers: getHeaders() }),
        fetch('/api/v1/tasks/metrics', { headers: getHeaders() }),
      ]);

      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setTasks(tasksData);
      }
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }
    } catch (err) {
      console.error('Failed to fetch queue data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
    const interval = setInterval(fetchQueueData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEnqueueTestTask = async (taskType: string) => {
    try {
      const res = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          task_type: taskType,
          payload: { initiated_by: 'ui-admin', timestamp: new Date().toISOString() },
          max_retries: 3,
        }),
      });
      if (!res.ok) throw new Error('Failed to enqueue task');
      await fetchQueueData();
    } catch (err: any) {
      alert(`Enqueue Error: ${err.message}`);
    }
  };

  const handleProcessTask = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/tasks/${id}/process`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to process task');
      await fetchQueueData();
    } catch (err: any) {
      alert(`Process Error: ${err.message}`);
    }
  };

  const handleCancelTask = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/tasks/${id}/cancel`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to cancel task');
      await fetchQueueData();
    } catch (err: any) {
      alert(`Cancel Error: ${err.message}`);
    }
  };

  const handleRetryTask = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/tasks/${id}/retry`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to retry task');
      await fetchQueueData();
    } catch (err: any) {
      alert(`Retry Error: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return { bg: '#dcfce7', color: '#166534', label: 'COMPLETED' };
      case 'RUNNING':
        return { bg: '#e0f2fe', color: '#0369a1', label: 'RUNNING' };
      case 'QUEUED':
        return { bg: '#fef3c7', color: '#92400e', label: 'QUEUED' };
      case 'FAILED':
        return { bg: '#fee2e2', color: '#991b1b', label: 'FAILED' };
      default:
        return { bg: '#f1f5f9', color: '#475569', label: 'CANCELLED' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Telemetry Metrics Header */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>ACTIVE WORKERS</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0284c7', marginTop: '0.2rem' }}>
            {metrics?.active_workers ?? 1}
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>QUEUED TASKS</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#d97706', marginTop: '0.2rem' }}>
            {metrics?.queued_tasks ?? 0}
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>RUNNING TASKS</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#2563eb', marginTop: '0.2rem' }}>
            {metrics?.running_tasks ?? 0}
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>COMPLETED TASKS</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#16a34a', marginTop: '0.2rem' }}>
            {metrics?.completed_tasks ?? 0}
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>FAILED TASKS</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#dc2626', marginTop: '0.2rem' }}>
            {metrics?.failed_tasks ?? 0}
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>
          ⚡ Background Execution Queue Monitor & Task Logs
        </h3>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleEnqueueTestTask('GITOPS_SYNC')}
            style={{ background: '#0284c7', color: '#ffffff', border: 'none', padding: '0.55rem 1rem', borderRadius: '6px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            ➕ Enqueue GitOps Sync Task
          </button>
          <button
            onClick={() => handleEnqueueTestTask('UNMANAGED_SWEEP')}
            style={{ background: '#4f46e5', color: '#ffffff', border: 'none', padding: '0.55rem 1rem', borderRadius: '6px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            ➕ Enqueue Unmanaged Sweep
          </button>
          <button
            onClick={fetchQueueData}
            style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', padding: '0.55rem 1rem', borderRadius: '6px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            🔄 Refresh Queue
          </button>
        </div>
      </div>

      {/* Queue Tasks Table */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc', color: '#475569', fontSize: '0.8rem', textTransform: 'uppercase', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '0.75rem 1.25rem' }}>Task ID</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Task Type</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Worker Node</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Retries</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Created At</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                    No background tasks in queue. Enqueue a task above to observe real-time background execution.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => {
                  const badge = getStatusBadge(task.status);
                  return (
                    <tr key={task.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '0.85rem 1.25rem', fontFamily: 'monospace', fontWeight: 600, color: '#0f172a' }}>
                        {task.id}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: '#0369a1' }}>
                        {task.task_type}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>
                        <span style={{ background: badge.bg, color: badge.color, padding: '0.2rem 0.5rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700 }}>
                          {badge.label}
                        </span>
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', color: '#64748b' }}>
                        <code>{task.worker_id}</code>
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', color: '#475569' }}>
                        {task.retry_count} / {task.max_retries}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', color: '#64748b', fontSize: '0.8rem' }}>
                        {new Date(task.created_at).toLocaleTimeString()}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>
                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                          {task.status === 'QUEUED' && (
                            <button
                              onClick={() => handleProcessTask(task.id)}
                              style={{ background: '#16a34a', color: '#ffffff', border: 'none', padding: '0.35rem 0.65rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                            >
                              ⚡ Process Now
                            </button>
                          )}
                          {task.status === 'FAILED' && (
                            <button
                              onClick={() => handleRetryTask(task.id)}
                              style={{ background: '#d97706', color: '#ffffff', border: 'none', padding: '0.35rem 0.65rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                            >
                              🔄 Retry
                            </button>
                          )}
                          {(task.status === 'QUEUED' || task.status === 'RUNNING') && (
                            <button
                              onClick={() => handleCancelTask(task.id)}
                              style={{ background: '#ef4444', color: '#ffffff', border: 'none', padding: '0.35rem 0.65rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                            >
                              🚫 Cancel
                            </button>
                          )}
                          <button
                            onClick={() => setSelectedTaskLog(task)}
                            style={{ background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', padding: '0.35rem 0.65rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                          >
                            📜 Logs
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

      {/* Task Execution Log Modal */}
      {selectedTaskLog && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.5rem', width: '90%', maxWidth: '650px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a' }}>
                📜 Background Task Log Inspector — {selectedTaskLog.id}
              </h3>
              <button
                onClick={() => setSelectedTaskLog(null)}
                style={{ background: 'transparent', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: '#64748b' }}
              >
                ✖
              </button>
            </div>

            <div style={{ background: '#0f172a', color: '#38bdf8', borderRadius: '8px', padding: '1rem', fontFamily: 'monospace', fontSize: '0.8rem', maxHeight: '350px', overflowY: 'auto' }}>
              <div>Task Type: {selectedTaskLog.task_type}</div>
              <div>Status: {selectedTaskLog.status}</div>
              <div>Worker Node: {selectedTaskLog.worker_id}</div>
              <div>Retries: {selectedTaskLog.retry_count} / {selectedTaskLog.max_retries}</div>
              <div style={{ marginTop: '0.5rem', color: '#94a3b8' }}>
                Payload: {JSON.stringify(selectedTaskLog.payload, null, 2)}
              </div>
              {selectedTaskLog.result && (
                <div style={{ marginTop: '0.5rem', color: '#4ade80' }}>
                  Result: {JSON.stringify(selectedTaskLog.result, null, 2)}
                </div>
              )}
              {selectedTaskLog.error_log && (
                <div style={{ marginTop: '0.5rem', color: '#f87171' }}>
                  Error Output: {selectedTaskLog.error_log}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button
                onClick={() => setSelectedTaskLog(null)}
                style={{ background: '#0f172a', color: '#ffffff', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
              >
                Close Log Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
