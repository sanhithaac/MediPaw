import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import ImageUploadZone from '../components/ImageUploadZone';
import './IntakePage.css';

const STEPS = ['Patient Info', 'Upload Images', 'Review & Submit'];

const UPLOAD_SLOTS = [
  {
    key:   'skin',
    label: 'Skin / Coat Image',
    icon:  '🧬',
    hint:  'Broad body shot for dermatological & wound check',
    model: 'CNN 1 + YOLOv8 + U-Net',
  },
  {
    key:   'ocular',
    label: 'Ocular Close-up',
    icon:  '👁️',
    hint:  'Macro close-up of the eyes (ulcer, cataract, lump)',
    model: 'CNN 2 → Eye CNN Classifier',
  },
  {
    key:   'membrane',
    label: 'Mucous Membrane / Gums',
    icon:  '💊',
    hint:  'Tight macro of lips/gums for perfusion check',
    model: 'CNN 3 → Systemic Perfusion Proxy',
  },
  {
    key:   'thoracic',
    label: 'Thoracic Radiograph',
    icon:  '🩻',
    hint:  'Latero-lateral chest X-ray for cardiothoracic geometry',
    model: 'Thoracic CNN → VHS & Radiograph Analysis',
  },
];

export default function IntakePage() {
  const navigate = useNavigate();
  const [step, setStep]       = useState(0);
  const [submitting, setSub]  = useState(false);

  const [info, setInfo] = useState({
    species: 'Dog',
    age: '',
    shelter: '',
    weight: '',
    notes: '',
  });

  const [images, setImages] = useState({
    skin: null,
    ocular: null,
    membrane: null,
    thoracic: null,
  });

  const updateInfo = (k, v) => setInfo(p => ({ ...p, [k]: v }));
  const setFile    = (k, f) => setImages(p => ({ ...p, [k]: f }));
  const removeFile = (k)    => setImages(p => ({ ...p, [k]: null }));

  const uploadedCount = Object.values(images).filter(Boolean).length;
  const canProceedStep1 = info.shelter.trim() && info.age.trim();
  const canProceedStep2 = uploadedCount > 0;

  const handleNext = () => {
    if (step === 0 && !canProceedStep1) {
      toast.error('Please fill in Shelter ID and Age');
      return;
    }
    if (step === 1 && !canProceedStep2) {
      toast.error('Please upload at least one image to analyze');
      return;
    }
    setStep(s => s + 1);
  };

  const handleSubmit = async () => {
    setSub(true);
    toast.loading('Uploading and running multi-modal AI models…', { id: 'submit' });

    const formData = new FormData();
    formData.append('species', info.species);
    formData.append('age', info.age);
    formData.append('shelter', info.shelter);
    formData.append('weight', info.weight);
    formData.append('notes', info.notes);

    if (images.skin) formData.append('skin_image', images.skin);
    if (images.ocular) formData.append('ocular_image', images.ocular);
    if (images.membrane) formData.append('membrane_image', images.membrane);
    if (images.thoracic) formData.append('thoracic_image', images.thoracic);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/intake', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      sessionStorage.setItem('medipaw_last_result', JSON.stringify(data));
      toast.success('AI Analysis Complete!', { id: 'submit' });
      navigate(`/results/${data.case_id}`, { state: data });
    } catch (err) {
      console.error('Intake submission error:', err);
      toast.error(`Backend error: ${err.message}. Please verify the backend is running on port 8000.`, { id: 'submit' });
    } finally {
      setSub(false);
    }
  };

  const slideVariants = {
    enter: (d) => ({ x: d > 0 ? 80 : -80, opacity: 0 }),
    center: { x: 0, opacity: 1 },
    exit:  (d) => ({ x: d > 0 ? -80 : 80, opacity: 0 }),
  };

  return (
    <div className="intake-page">
      {/* Breadcrumb */}
      <motion.div
        className="intake-breadcrumb"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <span className="section-label">New Patient Intake</span>
      </motion.div>

      <div className="intake-layout">
        {/* ── Left: Step indicator ── */}
        <aside className="intake-sidebar">
          <div className="intake-sidebar-logo">
            <span className="is-logo-medi">Medi</span>
            <span className="is-logo-paw">paw</span>
          </div>
          <p className="intake-sidebar-subtitle">Multi-Modal Intake Packet</p>

          <div className="step-list">
            {STEPS.map((s, i) => (
              <div key={s} className={`step-item ${i < step ? 'done' : i === step ? 'active' : 'future'}`}>
                <div className="step-circle">
                  {i < step ? '✓' : i + 1}
                </div>
                <div className="step-info">
                  <p className="step-name">{s}</p>
                  <p className="step-sub">
                    {i === 0 ? 'Species, shelter, notes' :
                     i === 1 ? 'Skin · Eyes · Gums · X-Ray' :
                               'Submit for AI analysis'}
                  </p>
                </div>
                {i < STEPS.length - 1 && <div className="step-connector" />}
              </div>
            ))}
          </div>

          {/* Model pipeline badge */}
          <div className="intake-pipeline-badge glass-card">
            <p className="ipb-title">🧠 AI Pipeline</p>
            {['Eye CNN', 'YOLOv8', 'Thoracic CNN', 'Skin CNN', 'U-Net', 'ViT (Future)'].map(m => (
              <div key={m} className="ipb-model">
                <span className="ipb-dot" />
                <span>{m}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Right: Step content ── */}
        <main className="intake-main">
          <AnimatePresence mode="wait" custom={1}>
            {/* Step 0: Patient Info */}
            {step === 0 && (
              <motion.div
                key="step0"
                className="intake-form glass-card"
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                custom={1}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              >
                <h2 className="intake-form-title">Patient Information</h2>
                <p className="intake-form-sub">Basic intake data for the case file</p>

                <div className="form-grid">
                  <div className="form-field">
                    <label>Species *</label>
                    <div className="species-toggle">
                      {['Dog', 'Cat', 'Other'].map(sp => (
                        <button
                          key={sp}
                          type="button"
                          className={`species-btn ${info.species === sp ? 'active' : ''}`}
                          onClick={() => updateInfo('species', sp)}
                        >
                          {sp === 'Dog' ? '🐕' : sp === 'Cat' ? '🐈' : '🐾'} {sp}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="form-field">
                    <label htmlFor="shelter">Shelter / Rescue ID *</label>
                    <input id="shelter" className="form-input" placeholder="e.g. Shelter-A-001"
                      value={info.shelter} onChange={e => updateInfo('shelter', e.target.value)} />
                  </div>

                  <div className="form-field">
                    <label htmlFor="age">Approximate Age *</label>
                    <input id="age" className="form-input" placeholder="e.g. ~2 years"
                      value={info.age} onChange={e => updateInfo('age', e.target.value)} />
                  </div>

                  <div className="form-field">
                    <label htmlFor="weight">Weight (kg)</label>
                    <input id="weight" className="form-input" type="number" placeholder="e.g. 12.5"
                      value={info.weight} onChange={e => updateInfo('weight', e.target.value)} />
                  </div>

                  <div className="form-field full-width">
                    <label htmlFor="notes">Clinical Observations (optional)</label>
                    <textarea id="notes" className="form-input form-textarea"
                      placeholder="Describe visible symptoms, behaviour, history…"
                      value={info.notes} onChange={e => updateInfo('notes', e.target.value)} />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 1: Image Upload */}
            {step === 1 && (
              <motion.div
                key="step1"
                className="intake-form glass-card"
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                custom={1}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              >
                <h2 className="intake-form-title">Multi-Modal Image Intake</h2>
                <p className="intake-form-sub">
                  Upload images for active model assessment. Each image feeds a specialized diagnostic module.
                </p>

                <div className="upload-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
                  {UPLOAD_SLOTS.map(slot => (
                    <div key={slot.key} className="upload-slot glass-card">
                      <div className="upload-slot-model">
                        <span className="usm-badge">{slot.model}</span>
                      </div>
                      <ImageUploadZone
                        label={slot.label}
                        icon={slot.icon}
                        hint={slot.hint}
                        file={images[slot.key]}
                        onFileAccepted={(f) => setFile(slot.key, f)}
                        onRemove={() => removeFile(slot.key)}
                      />
                    </div>
                  ))}
                </div>

                <div className="upload-status" style={{ marginTop: '16px' }}>
                  {uploadedCount} / {UPLOAD_SLOTS.length} images uploaded
                  {canProceedStep2 && <span className="upload-ready" style={{ color: '#16a34a', fontWeight: 'bold' }}> ✓ Ready to proceed</span>}
                </div>
              </motion.div>
            )}

            {/* Step 2: Review */}
            {step === 2 && (
              <motion.div
                key="step2"
                className="intake-form glass-card"
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                custom={1}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              >
                <h2 className="intake-form-title">Review & Submit</h2>
                <p className="intake-form-sub">Confirm details before triggering AI analysis</p>

                <div className="review-grid">
                  <div className="review-section">
                    <p className="review-section-title">Patient Details</p>
                    {[
                      ['Species',  info.species || '—'],
                      ['Shelter',  info.shelter  || '—'],
                      ['Age',      info.age      || '—'],
                      ['Weight',   info.weight ? `${info.weight} kg` : '—'],
                    ].map(([k, v]) => (
                      <div key={k} className="review-row">
                        <span className="review-key">{k}</span>
                        <span className="review-val">{v}</span>
                      </div>
                    ))}
                    {info.notes && (
                      <div className="review-notes">
                        <p className="review-key">Observations</p>
                        <p className="review-notes-text">{info.notes}</p>
                      </div>
                    )}
                  </div>

                  <div className="review-section">
                    <p className="review-section-title">Images Uploaded</p>
                    <div className="review-images" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '10px' }}>
                      {UPLOAD_SLOTS.map(slot => (
                        <div key={slot.key} className="review-img-item">
                          {images[slot.key] ? (
                            <img
                              src={URL.createObjectURL(images[slot.key])}
                              alt={slot.label}
                              className="review-thumb"
                            />
                          ) : (
                            <div className="review-thumb-empty">Not provided</div>
                          )}
                          <p className="review-img-label">{slot.icon} {slot.label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="review-ai-notice">
                  <span>🧠</span>
                  <p>
                    Submitting will run active AI models: Eye CNN, YOLOv8 Wound Detector, and Thoracic CNN.
                    Estimated turnaround: ~1-3 seconds.
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation buttons */}
          <div className="intake-nav">
            {step > 0 && (
              <button type="button" className="btn-outline" onClick={() => setStep(s => s - 1)}>
                ← Back
              </button>
            )}
            <div style={{ flex: 1 }} />
            {step < STEPS.length - 1 ? (
              <motion.button
                type="button"
                className="btn-primary"
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleNext}
              >
                Continue →
              </motion.button>
            ) : (
              <motion.button
                type="button"
                className={`btn-primary ${submitting ? 'btn-loading' : ''}`}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting ? '⟳ Analyzing…' : '🚀 Run AI Analysis'}
              </motion.button>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
