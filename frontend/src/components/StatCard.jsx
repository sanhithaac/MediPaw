import { motion } from 'framer-motion';

const PRIORITY_META = {
  Critical: { color: '#ef4444', badgeBg: 'rgba(239,68,68,0.12)', label: 'Critical' },
  High: { color: '#f97316', badgeBg: 'rgba(249,115,22,0.12)', label: 'High' },
  Medium: { color: '#d4a30a', badgeBg: 'rgba(212,163,10,0.12)', label: 'Medium' },
  Low: { color: '#16a34a', badgeBg: 'rgba(22,163,74,0.12)', label: 'Low' },
};

export default function StatCard({ priority, count, label, delay = 0 }) {
  const meta = PRIORITY_META[priority] || PRIORITY_META.Low;

  return (
    <motion.div
      className="stat-card glass-card"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      style={{
        '--accent': meta.color,
        '--accent-badge': meta.badgeBg,
        borderLeftColor: meta.color,
        borderLeftWidth: '4px',
        borderLeftStyle: 'solid',
      }}
    >
      <div className="stat-card-header">
        <span className="stat-badge" style={{ background: meta.badgeBg, color: meta.color }}>
          {meta.label}
        </span>
      </div>

      <div className="stat-card-body">
        <motion.div
          className="stat-count"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: delay + 0.1 }}
          style={{ color: meta.color }}
        >
          {count}
        </motion.div>

        <p className="stat-label">{label}</p>
      </div>

      <style>{`
        .stat-card {
          padding: 18px 20px;
          position: relative;
          overflow: hidden;
          flex: 1;
          min-width: 160px;
          cursor: default;
        }
        .stat-card-header {
          display: flex;
          justify-content: flex-start;
          margin-bottom: 12px;
        }
        .stat-badge {
          display: inline-flex;
          align-items: center;
          padding: 3px 8px;
          border-radius: 999px;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .stat-card-body {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 12px;
        }
        .stat-count {
          font-family: 'Inter', 'Segoe UI', sans-serif;
          font-size: 2.35rem;
          font-weight: 800;
          line-height: 1;
          font-variant-numeric: tabular-nums;
        }
        .stat-label {
          font-size: 0.78rem;
          color: var(--text-muted);
          font-weight: 600;
          line-height: 1.4;
          text-align: right;
          max-width: 96px;
        }
      `}</style>
    </motion.div>
  );
}
