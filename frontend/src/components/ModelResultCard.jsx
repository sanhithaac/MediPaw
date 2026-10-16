import { useState } from 'react';
import { motion } from 'framer-motion';

export default function ModelResultCard({
  modelNum,
  title,
  subtitle,
  label,
  confidence,
  color = '#1a8a7a',
  icon,
  status = 'ok',
  statusBadge = null,
  imageUrl = null,
  warnings = [],
  diagnostics = null,
  activeModalities = null,
  urgencyScore = null,
  delay = 0,
  children
}) {
  const [showImage, setShowImage] = useState(false);
  const pct = (confidence !== null && confidence !== undefined && !isNaN(confidence))
    ? Math.round(confidence * 100)
    : null;

  // Determine status chip text and style
  let badgeText = statusBadge;
  let badgeBg = 'rgba(15, 23, 42, 0.04)';
  let badgeColor = 'var(--text-secondary)';

  if (!badgeText) {
    if (status === 'ok') {
      badgeText = 'Validated Model';
      badgeBg = 'rgba(34, 197, 94, 0.12)';
      badgeColor = '#16a34a';
    } else if (status === 'unvalidated_prototype' || status === 'awaiting_labels') {
      badgeText = 'Awaiting Labels';
      badgeBg = 'rgba(234, 179, 8, 0.15)';
      badgeColor = '#ca8a04';
    } else if (status === 'architecture_prototype') {
      badgeText = 'Architecture Prototype';
      badgeBg = 'rgba(99, 102, 241, 0.15)';
      badgeColor = '#6366f1';
    } else if (status === 'unavailable' || status === 'checkpoint_missing') {
      badgeText = 'Weights Missing';
      badgeBg = 'rgba(239, 68, 68, 0.1)';
      badgeColor = '#dc2626';
    } else if (status === 'untrained_fallback') {
      badgeText = 'Untrained Demo';
      badgeBg = 'rgba(249, 115, 22, 0.12)';
      badgeColor = '#ea580c';
    } else if (status === 'skipped') {
      badgeText = 'Skipped — No Embeddings';
      badgeBg = 'rgba(100, 116, 139, 0.15)';
      badgeColor = '#64748b';
    } else {
      badgeText = 'Module Active';
    }
  }

  const backendHost = 'http://127.0.0.1:8000';
  const fullImageUrl = imageUrl ? (imageUrl.startsWith('http') ? imageUrl : `${backendHost}${imageUrl}`) : null;

  return (
    <motion.div
      className="glass-card mrc"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      style={{
        '--c': color,
        borderLeftColor: color,
        borderLeftWidth: '4px',
        borderLeftStyle: 'solid',
        padding: '18px 20px',
      }}
    >
      <div className="mrc-header">
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span className="mrc-chip">Module {modelNum}</span>
          <span
            className="mrc-status-pill"
            style={{ background: badgeBg, color: badgeColor }}
          >
            {badgeText}
          </span>
        </div>
        <span className="mrc-icon">{icon}</span>
      </div>

      <h3 className="mrc-title">{title}</h3>
      <p className="mrc-subtitle">{subtitle}</p>

      {label && (
        <div
          className="mrc-result"
          style={{
            color,
            background: `${color}14`,
            border: `1px solid ${color}30`
          }}
        >
          {label}
        </div>
      )}

      {/* Urgency score bar for ViT fusion results */}
      {urgencyScore !== null && urgencyScore !== undefined && (
        <div className="mrc-conf" style={{ marginBottom: '8px' }}>
          <div className="mrc-conf-header">
            <span>Fusion Urgency Score</span>
            <strong style={{ color }}>{Math.round(urgencyScore * 100)}%</strong>
          </div>
          <div className="mrc-bar-track">
            <motion.div
              className="mrc-bar-fill"
              style={{ background: `linear-gradient(90deg, ${color}60, ${color})` }}
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(urgencyScore * 100)}%` }}
              transition={{ duration: 1, delay: delay + 0.25, ease: 'easeOut' }}
            />
          </div>
        </div>
      )}

      {/* Active modalities pills for ViT fusion cards */}
      {activeModalities && activeModalities.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>Fused:</span>
          {activeModalities.map((m, i) => (
            <span key={i} style={{
              fontSize: '0.68rem',
              padding: '2px 8px',
              borderRadius: '999px',
              background: `${color}18`,
              color,
              fontWeight: 600,
              border: `1px solid ${color}30`
            }}>{m}</span>
          ))}
        </div>
      )}

      {pct !== null ? (
        <div className="mrc-conf">
          <div className="mrc-conf-header">
            <span>Model Confidence</span>
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
      ) : (
        <div className="mrc-uncalibrated-note">
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            {status === 'ok' ? 'Quantitative regression score (confidence n/a)' : 'Confidence uncalibrated / not applicable'}
          </span>
        </div>
      )}

      {fullImageUrl && (
        <div className="mrc-preview-box" style={{ marginTop: '12px' }}>
          <button
            type="button"
            className="mrc-toggle-img-btn"
            onClick={() => setShowImage(!showImage)}
          >
            {showImage ? '▼ Hide Annotated Overlay' : '▶ View Model Overlay'}
          </button>
          {showImage && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              style={{ marginTop: '8px', borderRadius: '8px', overflow: 'hidden' }}
            >
              <img
                src={fullImageUrl}
                alt="Detection visualization"
                style={{ width: '100%', maxHeight: '200px', objectFit: 'contain', background: '#0f172a', borderRadius: '6px' }}
              />
            </motion.div>
          )}
        </div>
      )}

      {warnings && warnings.length > 0 && (
        <div className="mrc-warnings" style={{ marginTop: '10px' }}>
          {warnings.slice(0, 2).map((w, i) => (
            <p key={i} className="mrc-warn-text">
              ℹ️ {w}
            </p>
          ))}
        </div>
      )}

      {diagnostics && diagnostics.dimensions && (
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px' }}>
          Dimensions: {diagnostics.dimensions[0]}×{diagnostics.dimensions[1]}px
          {diagnostics.inference_time_ms ? ` · ${diagnostics.inference_time_ms}ms` : ''}
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
        .mrc-status-pill {
          display:inline-flex;
          align-items:center;
          padding:3px 8px;
          border-radius:999px;
          font-size:0.68rem;
          font-weight:600;
          letter-spacing:0.02em;
        }
        .mrc-icon { font-size:1.4rem; line-height:1; }
        .mrc-title { font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:700; margin-bottom:4px; color: var(--text); }
        .mrc-subtitle { font-size:0.8rem; color:var(--text-muted); margin-bottom:12px; }
        .mrc-result {
          display:inline-flex;
          align-items:center;
          padding:5px 12px;
          border-radius:8px;
          font-size:0.82rem;
          font-weight:700;
          margin-bottom:12px;
          line-height:1.3;
        }
        .mrc-conf-header { display:flex; justify-content:space-between; font-size:0.76rem; color:var(--text-secondary); margin-bottom:7px; }
        .mrc-bar-track { height:6px; border-radius:999px; background:rgba(15, 23, 42, 0.08); overflow:hidden; }
        .mrc-bar-fill { height:100%; border-radius:999px; }
        .mrc-uncalibrated-note { margin-bottom:8px; }
        .mrc-toggle-img-btn {
          background: rgba(15, 23, 42, 0.04);
          border: 1px solid rgba(15, 23, 42, 0.1);
          color: var(--text-secondary);
          font-size: 0.74rem;
          font-weight: 600;
          padding: 4px 10px;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .mrc-toggle-img-btn:hover {
          background: rgba(15, 23, 42, 0.08);
          color: var(--text);
        }
        .mrc-warn-text {
          font-size: 0.72rem;
          color: var(--text-muted);
          line-height: 1.35;
          margin-bottom: 4px;
        }
      `}</style>
    </motion.div>
  );
}
