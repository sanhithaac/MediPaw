const PRIORITY_META = {
  Critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.3)',  icon: '🚨', pulse: true  },
  High:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.3)', icon: '🔴', pulse: false },
  Medium:   { color: '#eab308', bg: 'rgba(234,179,8,0.12)',  border: 'rgba(234,179,8,0.3)',  icon: '🟡', pulse: false },
  Low:      { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.3)',  icon: '🟢', pulse: false },
};

export default function TriageBadge({ priority, size = 'md' }) {
  const meta = PRIORITY_META[priority] || PRIORITY_META.Low;
  const fs   = size === 'lg' ? '0.88rem' : '0.72rem';
  const pad  = size === 'lg' ? '6px 16px' : '3px 10px';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: pad,
        borderRadius: '100px',
        fontSize: fs,
        fontWeight: 700,
        letterSpacing: '0.04em',
        color: meta.color,
        background: meta.bg,
        border: `1px solid ${meta.border}`,
        boxShadow: `0 0 12px ${meta.bg}`,
        animation: meta.pulse ? 'badge-pulse 1.8s infinite' : 'none',
        whiteSpace: 'nowrap',
      }}
    >
      <span>{meta.icon}</span>
      {priority}
      <style>{`
        @keyframes badge-pulse {
          0%, 100% { box-shadow: 0 0 12px rgba(239,68,68,0.25); }
          50%       { box-shadow: 0 0 24px rgba(239,68,68,0.55), 0 0 40px rgba(239,68,68,0.15); }
        }
      `}</style>
    </span>
  );
}
