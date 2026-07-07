import { motion } from 'framer-motion';

export default function ModelResultCard({ modelNum, title, subtitle, label, confidence, color, icon, delay = 0, children }) {
  const pct = confidence ? Math.round(confidence * 100) : null;

  return (
    <motion.div
      className="glass-card mrc"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      style={{
        '--c': color || '#1a8a7a',
        borderLeftColor: color || '#1a8a7a',
        borderLeftWidth: '4px',
        borderLeftStyle: 'solid',
        padding: '18px 20px',
      }}
    >
      <div className="mrc-header">
        <span className="mrc-chip">CNN {modelNum}</span>
        <span className="mrc-icon">{icon}</span>
      </div>

      <h3 className="mrc-title">{title}</h3>
      <p className="mrc-subtitle">{subtitle}</p>

      {label && (
        <div className="mrc-result" style={{ color, background: `${color}12`, border: `1px solid ${color}24` }}>
          {label}
        </div>
      )}

      {pct !== null && (
        <div className="mrc-conf">
          <div className="mrc-conf-header">
            <span>Confidence</span>
            <strong style={{ color }}>{pct}%</strong>
          </div>
          <div className="mrc-bar-track">
            <motion.div
              className="mrc-bar-fill"
              style={{ background: `linear-gradient(90deg, ${color}60, ${color})` }}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 1, delay: delay + 0.25, ease: 'easeOut' }}
            />
          </div>
        </div>
      )}

      {children}

      <style>{`
        .mrc { cursor: default; }
        .mrc-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; gap:8px; }
        .mrc-chip {
          display:inline-flex;
          align-items:center;
          padding:3px 8px;
          border-radius:999px;
          background: rgba(15, 23, 42, 0.04);
          color: var(--text-secondary);
          font-size:0.72rem;
          font-weight:700;
          letter-spacing:0.04em;
          text-transform:uppercase;
        }
        .mrc-icon { font-size:1.4rem; line-height:1; }
        .mrc-title { font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:700; margin-bottom:4px; color: var(--text); }
        .mrc-subtitle { font-size:0.8rem; color:var(--text-muted); margin-bottom:12px; }
        .mrc-result {
          display:inline-flex;
          align-items:center;
          padding:4px 10px;
          border-radius:999px;
          font-size:0.78rem;
          font-weight:700;
          margin-bottom:12px;
        }
        .mrc-conf-header { display:flex; justify-content:space-between; font-size:0.76rem; color:var(--text-secondary); margin-bottom:7px; }
        .mrc-bar-track { height:6px; border-radius:999px; background:rgba(15, 23, 42, 0.08); overflow:hidden; }
        .mrc-bar-fill { height:100%; border-radius:999px; }
      `}</style>
    </motion.div>
  );
}
