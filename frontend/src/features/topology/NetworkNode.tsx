import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';

export const NetworkNode: React.FC<NodeProps> = ({ data, selected }) => {
  const subnets = (data as any).subnets;
  const subnetStr = subnets && subnets.length > 0 ? subnets[0].subnet : 'No CIDR';
  const isHighlighted = (data as any).isHighlighted;
  const isDimmed = (data as any).isDimmed;

  // Capacity estimate
  const allocated = (data as any).allocated_ips || ((data as any).containers_count ? (data as any).containers_count + 1 : 2);
  const total = (data as any).total_ips || 254;
  const usagePct = Math.min(Math.round((allocated / total) * 100), 100);

  return (
    <div
      style={{
        background: '#ffffff',
        color: '#0f172a',
        padding: '0.85rem 1.25rem',
        borderRadius: '8px',
        border: selected ? '2px solid #2563eb' : '2px solid #3b82f6',
        minWidth: '200px',
        boxShadow: selected
          ? '0 0 0 4px rgba(37, 99, 235, 0.25), 0 10px 15px -3px rgba(0, 0, 0, 0.15)'
          : isHighlighted
          ? '0 0 14px rgba(59, 130, 246, 0.5)'
          : '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        opacity: isDimmed ? 0.35 : 1,
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" position={Position.Top} id="top" style={{ background: '#2563eb' }} />
      <Handle type="target" position={Position.Left} id="left" style={{ background: '#2563eb' }} />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#2563eb', fontWeight: 700, letterSpacing: '0.05em' }}>
          Virtual Network
        </div>
        {selected && (
          <span style={{ fontSize: '0.65rem', background: '#dbeafe', color: '#1e40af', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 700 }}>
            SELECTED
          </span>
        )}
      </div>

      <div style={{ fontWeight: 700, fontSize: '1rem', marginTop: '0.2rem' }}>{(data as any).label}</div>
      <div style={{ fontSize: '0.75rem', color: '#0284c7', fontFamily: 'monospace', margin: '0.2rem 0', fontWeight: 600 }}>
        {subnetStr}
      </div>

      {/* IPAM Capacity Bar */}
      <div style={{ marginTop: '0.4rem', marginBottom: '0.4rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#64748b', marginBottom: '0.15rem' }}>
          <span>IPAM Allocated</span>
          <span style={{ fontWeight: 600 }}>{usagePct}%</span>
        </div>
        <div style={{ height: '4px', background: '#e2e8f0', borderRadius: '2px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${usagePct}%`,
              background: usagePct > 80 ? '#ef4444' : usagePct > 50 ? '#f59e0b' : '#3b82f6',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.5rem' }}>
        <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.15rem 0.4rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700 }}>
          {(data as any).driver || 'bridge'}
        </span>
        <span style={{ background: '#f1f5f9', color: '#475569', padding: '0.15rem 0.4rem', borderRadius: '4px', fontSize: '0.7rem' }}>
          {(data as any).scope || 'local'}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#2563eb' }} />
      <Handle type="source" position={Position.Right} id="right" style={{ background: '#2563eb' }} />
    </div>
  );
};
