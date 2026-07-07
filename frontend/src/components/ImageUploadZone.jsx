import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import './ImageUploadZone.css';

export default function ImageUploadZone({ label, icon, hint, onFileAccepted, file, onRemove }) {
  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) onFileAccepted(accepted[0]);
  }, [onFileAccepted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    multiple: false,
  });

  const preview = file ? URL.createObjectURL(file) : null;

  return (
    <div className="iuz-wrapper">
      <div className="iuz-header">
        <span className="iuz-icon">{icon}</span>
        <div>
          <p className="iuz-label">{label}</p>
          <p className="iuz-hint">{hint}</p>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {file ? (
          /* ── Preview state ── */
          <motion.div
            key="preview"
            className="iuz-preview"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.85 }}
            transition={{ duration: 0.3 }}
          >
            <img src={preview} alt="uploaded" className="iuz-img" />
            <div className="iuz-preview-info">
              <span className="iuz-filename">{file.name}</span>
              <span className="iuz-size">{(file.size / 1024).toFixed(1)} KB</span>
            </div>
            <button className="iuz-remove" onClick={onRemove} title="Remove image">✕</button>
            <div className="iuz-check">✓</div>
          </motion.div>
        ) : (
          /* ── Drop zone ── */
          <motion.div
            key="dropzone"
            {...getRootProps()}
            className={`iuz-zone ${isDragActive ? 'iuz-zone--active' : ''}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <input {...getInputProps()} />
            <div className="iuz-zone-inner">
              {isDragActive ? (
                <motion.div
                  animate={{ scale: [1, 1.15, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                >
                  <div className="iuz-drop-icon">📥</div>
                  <p className="iuz-drop-text">Drop it!</p>
                </motion.div>
              ) : (
                <>
                  <div className="iuz-upload-icon">⬆</div>
                  <p className="iuz-upload-primary">Drag & drop or click</p>
                  <p className="iuz-upload-sub">JPG, PNG, WEBP · Max 10MB</p>
                </>
              )}
            </div>

            {/* Scanning line animation */}
            <div className="iuz-scan-line" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
