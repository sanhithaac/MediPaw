import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import ModelResultCard from '../components/ModelResultCard';
import TriageBadge from '../components/TriageBadge';
import './ResultsPage.css';

/* ── Mock result data ── */
const MOCK_RESULT = {
  caseId:   'MP-DEMO',
  priority: 'Critical',
  species:  '🐕 Dog',
  age:      '~2 yr',
  shelter:  'Shelter-A-001',
  processed:'4.2 seconds',
  models: [
    {
      num:        1,
      title:      'Skin / Coat Classifier',
      subtitle:   'CNN 1 — Dermatological Analysis',
      label:      'Severe Mange',
      confidence: 0.93,
      color:      '#22c9b0',
      icon:       '🧬',
    },
    {
      num:        2,
      title:      'Ocular Pathology Classifier',
      subtitle:   'CNN 2 — Trauma & Vision Threats',
      label:      'Corneal Ulcer',
      confidence: 0.87,
      color:      '#6366f1',
      icon:       '👁️',
    },
    {
      num:        3,
      title:      'Mucous Membrane Classifier',
      subtitle:   'CNN 3 — Systemic Shock Proxy',
      label:      'Pale / Anemic',
      confidence: 0.91,
      color:      '#e8756a',
      icon:       '💊',
    },
    {
      num:        4,
      title:      'YOLOv8 Parasite Localizer',
      subtitle:   'Bounding-box tick/laceration map',
      label:      '3 Lesions Detected',
      confidence: 0.88,
      color:      '#f97316',
      icon:       '🎯',
    },
    {
      num:        5,
      title:      'U-Net Wound Geometry',
      subtitle:   'Pixel-level surface area masking',
      label:      '28.4% Tissue Damage',
      confidence: 0.85,
      color:      '#eab308',
      icon:       '🗺️',
    },
    {
      num:        6,
      title:      'ViT Decision Head',
      subtitle:   'Multi-modal fusion + triage override',
      label:      '⚠️ Rule Override: Critical (Pale gums)',
      confidence: 0.97,
      color:      '#22c55e',
      icon:       '🧠',
    },
  ],
  reasoning:
    'Pale mucous membranes indicate systemic vascular shock / anemia — safety override triggered. ' +
    'Combined with severe mange (93%), active corneal ulcer (87%), and 28.4% wound surface area, ' +
    'the ViT head escalated the final triage score to CRITICAL regardless of the individual skin score.',
};

const PRIORITY_BG = {
  Critical: 'rgba(239,68,68,0.08)',
  High:     'rgba(249,115,22,0.08)',
  Medium:   'rgba(234,179,8,0.08)',
  Low:      'rgba(34,197,94,0.08)',
};

export default function ResultsPage() {
  // eslint-disable-next-line no-unused-vars
  const { caseId } = useParams();
  const navigate   = useNavigate();
  const d          = MOCK_RESULT; // In production: fetch by caseId

  return (
    <div className="results-page">
      {/* ── Back ── */}
      <motion.button
        className="btn-outline results-back"
        onClick={() => navigate('/')}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        ← Back to Queue
      </motion.button>

      {/* ── Priority Hero Banner ── */}
      <motion.section
        className="results-hero"
        style={{ background: PRIORITY_BG[d.priority] }}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Animated glow ring behind badge */}
        <div className="results-hero-glow" />

        <div className="results-hero-left">
          <span className="section-label">AI Triage Result · {d.caseId}</span>
          <h1 className="results-hero-title">Treatment Priority Score</h1>
          <div className="results-badge-wrap">
            <TriageBadge priority={d.priority} size="lg" />
          </div>
          <p className="results-reasoning">{d.reasoning}</p>
        </div>

        <div className="results-hero-right">
          {[
            ['Species',        d.species   ],
            ['Age',            d.age       ],
            ['Shelter',        d.shelter   ],
            ['AI Process Time',d.processed ],
            ['Models Run',     '6 / 6 ✓'  ],
          ].map(([k, v]) => (
            <div key={k} className="results-meta-row">
              <span className="rmr-key">{k}</span>
              <span className="rmr-val">{v}</span>
            </div>
          ))}
        </div>
      </motion.section>

      {/* ── Model Output Grid ── */}
      <motion.section
        className="results-models-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 0.6 }}
      >
        <div className="results-section-header">
          <h2>6-Model Pipeline Output</h2>
          <p>Individual classification results from each AI module</p>
        </div>

        <div className="results-models-grid">
          {d.models.map((m, i) => (
            <ModelResultCard
              key={m.num}
              modelNum={m.num}
              title={m.title}
              subtitle={m.subtitle}
              label={m.label}
              confidence={m.confidence}
              color={m.color}
              icon={m.icon}
              delay={i * 0.08}
            />
          ))}
        </div>
      </motion.section>

      {/* ── ViT Reasoning ── */}
      <motion.section
        className="results-reasoning-card glass-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
      >
        <div className="rrc-header">
          <span className="rrc-icon">🧠</span>
          <div>
            <h3>ViT Decision Head — Clinical Reasoning</h3>
            <p>Rule-override logic + multi-modal feature fusion summary</p>
          </div>
        </div>
        <div className="rrc-body">
          <div className="rrc-rule-override">
            <span className="rrc-rule-badge">⚡ SAFETY OVERRIDE ACTIVE</span>
            <p>Pale / Anemic gum classification detected → Priority escalated to CRITICAL regardless of individual model scores.</p>
          </div>
          <div className="rrc-features">
            {[
              { label: 'Skin Pathology Weight',   val: '93%', color: '#22c9b0' },
              { label: 'Ocular Risk Weight',       val: '87%', color: '#6366f1' },
              { label: 'Shock Proxy Weight',       val: '91%', color: '#ef4444' },
              { label: 'Wound Area Penalty',       val: '28.4% SA', color: '#f97316' },
              { label: 'ViT Fusion Confidence',   val: '97%', color: '#22c55e' },
            ].map(f => (
              <div key={f.label} className="rrc-feature-row">
                <span className="rrcf-label">{f.label}</span>
                <span className="rrcf-val" style={{ color: f.color }}>{f.val}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ── Actions ── */}
      <motion.div
        className="results-actions"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
      >
        <button className="btn-outline" onClick={() => navigate('/intake')}>
          + New Intake
        </button>
        <button className="btn-primary">
          📋 Export Report (PDF)
        </button>
      </motion.div>
    </div>
  );
}
