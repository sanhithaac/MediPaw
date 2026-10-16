import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import ModelResultCard from '../components/ModelResultCard';
import TriageBadge from '../components/TriageBadge';
import './ResultsPage.css';

const PRIORITY_BG = {
  Critical: 'rgba(239, 68, 68, 0.08)',
  High:     'rgba(249, 115, 22, 0.08)',
  Medium:   'rgba(234, 179, 8, 0.08)',
  Low:      'rgba(34, 197, 94, 0.08)',
};

export default function ResultsPage() {
  const { caseId } = useParams();
  const navigate   = useNavigate();
  const location   = useLocation();

  // 1. Retrieve real intake result from router state or sessionStorage
  let liveData = location.state;
  if (!liveData) {
    try {
      const stored = sessionStorage.getItem('medipaw_last_result');
      if (stored) liveData = JSON.parse(stored);
    } catch (e) {
      console.warn('Failed to parse cached result', e);
    }
  }

  // 2. Fallback display if accessed directly without submission
  const isDemo = !liveData;
  const d = liveData || {
    case_id: caseId || 'MP-DEMO',
    priority: 'High',
    patient: {
      species: 'Dog',
      age: '~2 yr',
      shelter: 'Shelter-A-001',
      weight: '12.5',
      notes: 'Demo case file'
    },
    processed_time_sec: 1.85,
    triage_rationale: 'Demonstration triage result. Submit an intake packet to run live AI models on your images.',
    models: [
      {
        model_name: 'Eye CNN (Ocular Pathology)',
        prediction: 'Conjunctivitis',
        confidence: 0.942,
        status: 'ok',
        warnings: []
      },
      {
        model_name: 'YOLOv8 Wound Detector',
        prediction: '2 Lesions Localized',
        confidence: 0.814,
        status: 'ok',
        warnings: []
      },
      {
        model_name: 'Thoracic CNN (Canine Radiograph)',
        prediction: 'Awaiting Clinical Ground-Truth Annotations (PMC8111263)',
        confidence: null,
        status: 'unvalidated_prototype',
        warnings: ['Thoracic dataset contains 153 unannotated radiographs without verified VHS labels.']
      },
      {
        model_name: 'Skin CNN (Dermatological Pathology)',
        prediction: 'Trained Checkpoint Not Present Locally',
        confidence: null,
        status: 'unavailable',
        warnings: ['Model architecture exists; trained weights from Colab are not in local workspace.']
      },
      {
        model_name: 'U-Net + YOLOv8 Wound Segmenter',
        prediction: 'Demonstration Fallback (Untrained Weights)',
        confidence: null,
        status: 'untrained_fallback',
        warnings: ['U-Net weights missing. Bounding boxes are from YOLO, not ground truth pixel masks.']
      },
      {
        model_name: 'Multi-Modal ViT (Fusion Layer)',
        task: 'Cross-Modal Feature Fusion & Triage Urgency Estimation',
        prediction: 'Architecture Prototype — Untrained Weights',
        confidence: null,
        status: 'architecture_prototype',
        active_modalities: [],
        urgency_score: null,
        warnings: ['Multi-Modal ViT architecture is implemented with 3-layer Transformer encoder. Supervised training on multi-modal clinical cohorts is required before producing operational triage scores.']
      }
    ]
  };

  const priority = d.priority || 'Medium';
  const models = d.models || [];

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
        style={{ background: PRIORITY_BG[priority] || PRIORITY_BG.Medium }}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="results-hero-glow" />

        <div className="results-hero-left">
          <span className="section-label">
            AI Triage Result · {d.case_id} {isDemo ? '(Demo File)' : '· Live Pipeline'}
          </span>
          <h1 className="results-hero-title">Treatment Priority Score</h1>
          <div className="results-badge-wrap">
            <TriageBadge priority={priority} size="lg" />
          </div>
          <p className="results-reasoning">{d.triage_rationale}</p>
        </div>

        <div className="results-hero-right">
          {[
            ['Species',         d.patient?.species || 'Dog'],
            ['Age',             d.patient?.age     || '—'],
            ['Shelter',         d.patient?.shelter || '—'],
            ['AI Turnaround',   `${d.processed_time_sec || 1.2}s`],
            ['Active Models',   `${models.length} Evaluated`],
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
          <h2>Active AI Model Diagnostics</h2>
          <p>Verified model predictions, quantitative regression, and data integrity notices</p>
        </div>

        <div className="results-models-grid">
          {models.map((m, i) => {
            let icon = '🔬';
            let color = '#0284c7';
            const name = m.model_name || `Model ${i + 1}`;

            if (name.includes('Eye')) {
              icon = '👁️';
              color = '#6366f1';
            } else if (name.includes('YOLO')) {
              icon = '🎯';
              color = '#f97316';
            } else if (name.includes('Thoracic')) {
              icon = '🩻';
              color = '#0284c7';
            } else if (name.includes('Skin')) {
              icon = '🧬';
              color = '#14b8a6';
            } else if (name.includes('U-Net')) {
              icon = '🗺️';
              color = '#eab308';
            } else if (name.includes('Membrane') || name.includes('Perfusion')) {
              icon = '💊';
              color = '#ef4444';
            } else if (name.includes('ViT') || name.includes('Fusion') || name.includes('Multi-Modal')) {
              icon = '🧠';
              color = '#8b5cf6';
            }

            return (
              <ModelResultCard
                key={i}
                modelNum={i + 1}
                title={name}
                subtitle={m.task || 'Veterinary Diagnostic Module'}
                label={m.prediction || 'No output recorded'}
                confidence={m.confidence}
                color={color}
                icon={icon}
                status={m.status || 'ok'}
                imageUrl={m.visualization_url || m.overlay_url || null}
                warnings={m.warnings || []}
                diagnostics={m.diagnostics || null}
                activeModalities={m.active_modalities || null}
                urgencyScore={m.urgency_score ?? null}
                delay={i * 0.08}
              />
            );
          })}
        </div>
      </motion.section>

      {/* ── Clinical Decision Support Notice ── */}
      <motion.section
        className="results-reasoning-card glass-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
      >
        <div className="rrc-header">
          <span className="rrc-icon">🧠</span>
          <div>
            <h3>Multi-Modal Vision Transformer (ViT) & Clinical Decision-Support</h3>
            <p>Fusion architecture design & protocol disclosure</p>
          </div>
        </div>
        <div className="rrc-body">
          <div className="rrc-rule-override" style={{ borderColor: 'rgba(234, 179, 8, 0.4)', background: 'rgba(234, 179, 8, 0.06)' }}>
            <span className="rrc-rule-badge" style={{ background: '#ca8a04', color: '#fff' }}>
              🔬 CLINICAL DECISION-SUPPORT PROTOTYPE
            </span>
            <p style={{ marginTop: '8px' }}>
              MediPaw is engineered as an auxiliary decision-support tool for veterinary triage queues.
              It does not replace professional physical examination or clinical diagnosis.
            </p>
          </div>
          <div className="rrc-features" style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <strong>Multi-Modal ViT Status:</strong> Active CNN backbones (Eye CNN and Thoracic CNN)
              extract standardized 576-dimensional intermediate embeddings via LayerNorm feature heads.
              These embeddings are architected for a downstream cross-modal Transformer fusion layer.
              In accordance with scientific rigor, arbitrary confidence summing is prohibited, and the
              future fusion layer will be trained on multi-modal clinical cohorts before producing autonomous triage scores.
            </p>
          </div>
        </div>
      </motion.section>

      {/* ── Actions ── */}
      <motion.div
        className="results-actions"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        style={{ marginTop: '24px', display: 'flex', gap: '12px' }}
      >
        <button type="button" className="btn-outline" onClick={() => navigate('/intake')}>
          + New Patient Intake
        </button>
        <button type="button" className="btn-primary" onClick={() => window.print()}>
          📋 Print Patient Summary
        </button>
      </motion.div>
    </div>
  );
}
