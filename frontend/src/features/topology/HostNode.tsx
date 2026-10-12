import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';

export const HostNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isDimmed = (data as any).isDimmed;
  const isHighlighted = (data as any).isHighlighted;

  return (
    <div
      style={{
        background: '#0f172a',
        color: '#ffffff',
        padding: '0.85rem 1.25rem',
        borderRadius: '8px',
        border: selected ? '2px solid #38bdf8' : '2px solid #0284c7',
        minWidth: '180px',
        boxShadow: selected
          ? '0 0 0 4px rgba(56, 189, 248, 0.3), 0 10px 15px -3px rgba(0, 0, 0, 0.4)'
          : isHighlighted
          ? '0 0 14px rgba(56, 189, 248, 0.6)'
          : '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
        opacity: isDimmed ? 0.35 : 1,
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#38bdf8', fontWeight: 700, letterSpacing: '0.05em' }}>
          Infrastructure Host
        </div>
        {selected && (
          <span style={{ fontSize: '0.65rem', background: '#0369a1', color: '#e0f2fe', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 700 }}>
            SELECTED
          </span>
        )}
      </div>

      <div style={{ fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>{(data as any).label}</div>
      {(data as any).sublabel && <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>{(data as any).sublabel}</div>}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #1e293b' }}>
        <span style={{ fontSize: '0.7rem', background: (data as any).status === 'ONLINE' || (data as any).status === 'HEALTHY' ? '#166534' : '#991b1b', color: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '4px', fontWeight: 600 }}>
          {(data as any).status || 'HEALTHY'}
        </span>
        <span style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 600 }}>{(data as any).environment || 'production'}</span>
      </div>
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#38bdf8' }} />
      <Handle type="source" position={Position.Right} id="right" style={{ background: '#38bdf8' }} />
    </div>
  );
};

export const HostGroupNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isDimmed = (data as any).isDimmed;

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.05)',
        color: '#0f172a',
        padding: '1rem',
        borderRadius: '12px',
        border: selected ? '2px solid #0284c7' : '2px dashed #0284c7',
        minWidth: '240px',
        opacity: isDimmed ? 0.35 : 1,
        transition: 'all 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em' }}>
          🖥️ Host Group: {(data as any).label}
        </span>
        <span style={{ fontSize: '0.7rem', background: '#e0f2fe', color: '#0369a1', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: 600 }}>
          {(data as any).environment || 'fleet'}
        </span>
      </div>
      <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>{(data as any).sublabel}</div>
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#0284c7' }} />
      <Handle type="source" position={Position.Right} id="right" style={{ background: '#0284c7' }} />
    </div>
  );
};
