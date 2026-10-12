import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';

export const ContainerNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isRunning = (data as any).status === 'running';
  const isHighlighted = (data as any).isHighlighted;
  const isDimmed = (data as any).isDimmed;

  return (
    <div
      style={{
        background: '#ffffff',
        color: '#0f172a',
        padding: '0.75rem 1rem',
        borderRadius: '8px',
        border: selected ? '2px solid #0284c7' : `2px solid ${isRunning ? '#16a34a' : '#94a3b8'}`,
        minWidth: '170px',
        boxShadow: selected
          ? '0 0 0 4px rgba(2, 132, 199, 0.25), 0 10px 15px -3px rgba(0, 0, 0, 0.1)'
          : isHighlighted
          ? '0 0 12px rgba(34, 197, 94, 0.4)'
          : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        opacity: isDimmed ? 0.35 : 1,
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" position={Position.Top} id="top" style={{ background: isRunning ? '#16a34a' : '#94a3b8' }} />
      <Handle type="target" position={Position.Left} id="left" style={{ background: isRunning ? '#16a34a' : '#94a3b8' }} />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: isRunning ? '#15803d' : '#64748b', fontWeight: 700, letterSpacing: '0.04em' }}>
          Workload Container
        </div>
        {selected && (
          <span style={{ fontSize: '0.65rem', background: '#e0f2fe', color: '#0369a1', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 700 }}>
            SELECTED
          </span>
        )}
      </div>

      <div style={{ fontWeight: 700, fontSize: '0.95rem', marginTop: '0.15rem' }}>{(data as any).label}</div>

      {(data as any).ip_address && (
        <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#0284c7', marginTop: '0.2rem', fontWeight: 600 }}>
          {(data as any).ip_address}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.4rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isRunning ? '#22c55e' : '#94a3b8',
              boxShadow: isRunning ? '0 0 6px #22c55e' : 'none',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{(data as any).status || 'unknown'}</span>
        </div>
        {(data as any).environment && (
          <span style={{ fontSize: '0.65rem', color: '#64748b', background: '#f1f5f9', padding: '0.1rem 0.35rem', borderRadius: '3px' }}>
            {(data as any).environment}
          </span>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: isRunning ? '#16a34a' : '#94a3b8' }} />
    </div>
  );
};
