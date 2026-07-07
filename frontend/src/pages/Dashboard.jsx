import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import TriageBadge from '../components/TriageBadge';
import OrganicTriageCard from '../components/OrganicTriageCard';
import './Dashboard.css';

/* ── Mock triage queue ── */
const MOCK_CASES = [
  { id: 'MP-001', species: '🐕 Dog',  age: '~2 yr',  priority: 'Critical', condition: 'Severe Mange + Corneal Ulcer + Pale Gums',   shelter: 'Shelter A', time: '8 min ago'  },
  { id: 'MP-002', species: '🐕 Dog',  age: '~5 yr',  priority: 'High',     condition: 'Tick Infestation + Conjunctivitis',           shelter: 'Shelter B', time: '15 min ago' },
  { id: 'MP-003', species: '🐈 Cat',  age: '~1 yr',  priority: 'Critical', condition: 'Hypoxic Gums + Deep Laceration (32% SA)',     shelter: 'Shelter A', time: '29 min ago' },
  { id: 'MP-004', species: '🐕 Dog',  age: '~3 yr',  priority: 'Medium',   condition: 'Ringworm + Mild Conjunctivitis',              shelter: 'Shelter C', time: '52 min ago' },
  { id: 'MP-005', species: '🐕 Dog',  age: '~7 yr',  priority: 'High',     condition: 'Cataract + Skin Dermatitis',                 shelter: 'Shelter B', time: '1.2 hr ago' },
  { id: 'MP-006', species: '🐈 Cat',  age: '~4 yr',  priority: 'Low',      condition: 'Minor Dermatitis — Monitor',                 shelter: 'Shelter A', time: '2.1 hr ago' },
  { id: 'MP-007', species: '🐕 Dog',  age: '~6 yr',  priority: 'Medium',   condition: 'Flea Cluster + Mild Skin Irritation',        shelter: 'Shelter D', time: '3.4 hr ago' },
];

const STATS = [
  { priority: 'Critical', count: 2, label: 'Require Immediate Attention' },
  { priority: 'High',     count: 2, label: 'High-Priority Cases' },
  { priority: 'Medium',   count: 2, label: 'Monitor Closely' },
  { priority: 'Low',      count: 1, label: 'Routine Follow-up' },
];

/* ── Animated counter ── */
function Counter({ target, duration = 1500 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const pct = Math.min((ts - start) / duration, 1);
      setVal(Math.floor(pct * target));
      if (pct < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return <span>{val}</span>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('All');
  const [cursorGlow, setCursorGlow] = useState({ x: 0, y: 0, active: false });
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  const priorities = ['All', 'Critical', 'High', 'Medium', 'Low'];
  const filtered = filter === 'All' ? MOCK_CASES : MOCK_CASES.filter(c => c.priority === filter);

  const handleCursorMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setCursorGlow({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      active: true,
    });
  };

  const handleCursorLeave = () => {
    setCursorGlow((prev) => ({ ...prev, active: false }));
    setParallax({ x: 0, y: 0 });
  };

  const handleHeroMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setParallax({ x: x * 6, y: y * 6 });
  };

  return (
    <div
      className="dashboard"
      onMouseMove={handleCursorMove}
      onMouseLeave={handleCursorLeave}
      style={{ '--cursor-x': `${cursorGlow.x}px`, '--cursor-y': `${cursorGlow.y}px` }}
    >
      <div className={`dashboard-cursor-glow ${cursorGlow.active ? 'is-active' : ''}`} />
      {/* ── Hero ── */}
      <motion.section
        className="dash-hero"
        initial={{ opacity: 0, y: -24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        onMouseMove={handleHeroMove}
        onMouseLeave={handleCursorLeave}
      >
        <motion.div
          className="dash-hero-left"
          animate={{ x: parallax.x * 0.5, y: parallax.y * 0.4, rotateX: parallax.y * -0.3, rotateY: parallax.x * 0.3 }}
          transition={{ type: 'spring', stiffness: 80, damping: 18, mass: 0.6 }}
        >
          <span className="section-label">AI Triage Dashboard</span>
          <h1 className="dash-title">
            Shelter Triage<br />
            <span className="gradient-text">Command Center</span>
          </h1>
          <p className="dash-desc">
            Real-time AI-powered triage queue. Multi-organ distress analysis across 6 deep-learning models.
          </p>
          <div className="dash-hero-actions">
            <motion.button
              className="btn-primary"
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/intake')}
            >
              <span>＋</span> New Patient Intake
            </motion.button>
            <div className="dash-live-indicator">
              <span className="live-dot" />
              <span>Live Updates</span>
            </div>
          </div>
        </motion.div>

        {/* ── Aggregate metrics ── */}
        <motion.div
          className="dash-hero-right"
          animate={{ x: parallax.x * -0.35, y: parallax.y * -0.28, rotateX: parallax.y * 0.2, rotateY: parallax.x * -0.2 }}
          transition={{ type: 'spring', stiffness: 80, damping: 18, mass: 0.6 }}
        >
          <div className="dash-metric-card glass-card">
            <p className="dash-metric-label">Cases Today</p>
            <div className="dash-metric-val teal-text">
              <Counter target={7} />
            </div>
            <div className="dash-metric-bar">
              <motion.div
                style={{ width: '100%', background: 'linear-gradient(90deg,#1a9e8b,#e8756a)' }}
                initial={{ width: 0 }}
                animate={{ width: '100%' }}
                transition={{ duration: 1.2, ease: 'easeOut', delay: 0.4 }}
              />
            </div>
          </div>
          <div className="dash-metric-card glass-card">
            <p className="dash-metric-label">Avg. AI Score Time</p>
            <div className="dash-metric-val coral-text">
              <Counter target={4} duration={1000} /><span className="dash-metric-unit">s</span>
            </div>
          </div>
          <div className="dash-metric-card glass-card">
            <p className="dash-metric-label">Models Active</p>
            <div className="dash-metric-val teal-text">
              <Counter target={6} duration={900} />
            </div>
          </div>
        </motion.div>
      </motion.section>

      {/* ── Triage widget arch ── */}
      <motion.section
        style={{ width: '100%', display: 'flex', justifyContent: 'center', overflowX: 'auto', padding: '32px 16px' }}
        initial={{ opacity: 0, y: 28, rotateX: 10 }}
        whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'nowrap', alignItems: 'flex-end', justifyContent: 'center', gap: '20px', minWidth: 'min-content' }}>
          {STATS.map((s, i) => {
            const offsetClass =
              i === 0
                ? 'translate-y-4'
                : i === 1 || i === 2
                  ? '-translate-y-3'
                  : 'translate-y-4';

            const accentStyles = {
              Critical: { borderColor: '#a73636', badgeColor: '#991b1b', badgeBg: '#fee2e2' },
              High: { borderColor: '#f49c5c', badgeColor: '#92400e', badgeBg: '#ffedd5' },
              Medium: { borderColor: '#f3d39e', badgeColor: '#92400e', badgeBg: '#fef3c7' },
              Low: { borderColor: '#7cf6c9', badgeColor: '#065f46', badgeBg: '#d1fae5' },
            };

            return (
              <OrganicTriageCard
                key={s.priority}
                stat={s}
                index={i}
                offsetClass={offsetClass}
                accentStyle={accentStyles[s.priority]}
              />
            );
          })}
        </div>
      </motion.section>

      {/* ── Triage queue ── */}
      <motion.section
        className="dash-queue"
        initial={{ opacity: 0, y: 32, rotateX: 8 }}
        whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.65, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="dash-queue-header">
          <div>
            <h2>Active Triage Queue</h2>
            <p>{filtered.length} case{filtered.length !== 1 ? 's' : ''} {filter !== 'All' ? `· ${filter}` : ''}</p>
          </div>
          <div className="dash-filters">
            {priorities.map(p => (
              <button
                key={p}
                className={`dash-filter-btn ${filter === p ? 'dash-filter-btn--active' : ''}`}
                onClick={() => setFilter(p)}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="dash-table-wrap glass-card">
          <table className="dash-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Species</th>
                <th>Age</th>
                <th>Priority</th>
                <th>AI Findings</th>
                <th>Shelter</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c, i) => (
                <motion.tr
                  key={c.id}
                  className="dash-row"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  onClick={() => navigate(`/results/${c.id}`)}
                >
                  <td><span className="case-id">{c.id}</span></td>
                  <td>{c.species}</td>
                  <td className="muted">{c.age}</td>
                  <td><TriageBadge priority={c.priority} /></td>
                  <td className="condition-cell">{c.condition}</td>
                  <td className="muted">{c.shelter}</td>
                  <td className="muted">{c.time}</td>
                  <td>
                    <button className="dash-view-btn">View →</button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.section>

      {/* ── Pipeline info strip ── */}
      <motion.section
        className="dash-pipeline"
        initial={{ opacity: 0, y: 24, rotateX: 8 }}
        whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ delay: 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        {[
          { num: 1, label: 'Skin/Coat CNN',      icon: '🧬', color: '#22c9b0' },
          { num: 2, label: 'Ocular CNN',          icon: '👁️', color: '#6366f1' },
          { num: 3, label: 'Membrane CNN',        icon: '💊', color: '#e8756a' },
          { num: 4, label: 'YOLOv8 Localizer',   icon: '🎯', color: '#f97316' },
          { num: 5, label: 'U-Net Geometry',      icon: '🗺️', color: '#eab308' },
          { num: 6, label: 'ViT Decision Head',   icon: '🧠', color: '#22c55e' },
        ].map((m, i) => (
          <motion.div
            key={m.num}
            className="pipeline-step glass-card"
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 + i * 0.07, duration: 0.45 }}
            whileHover={{ scale: 1.04, translateZ: '10px' }}
          >
            <div className="pipeline-num" style={{ color: m.color, borderColor: m.color, boxShadow: `0 0 8px ${m.color}60` }}>
              {m.num}
            </div>
            <div className="pipeline-icon">{m.icon}</div>
            <p className="pipeline-label">{m.label}</p>
            <div className="pipeline-active-dot" style={{ background: m.color }} />
          </motion.div>
        ))}
      </motion.section>
    </div>
  );
}
