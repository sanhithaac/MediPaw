import { useEffect, useRef, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import './Logo3DSplash.css';

const LAYERS = 4;

const FLOATER_EMOJIS = ['🐾', '🦴', '❤️', '🐾', '💊', '🐾', '🦴', '❤️', '🐾', '🦴', '💉', '🐾'];

export default function Logo3DSplash({ onComplete }) {
  const [phase, setPhase] = useState('intro'); // intro → assemble → idle → exit
  const groupRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const currentRot = useRef({ x: 0, y: 0 });
  const rafRef = useRef(null);

  // Generate randomized positions that remain stable across renders
  const floaters = useMemo(() => {
    return FLOATER_EMOJIS.map((emoji) => {
      // Keep floaters mostly around outer regions to avoid overlapping the central logo
      const side = Math.random() > 0.5;
      const left = side ? (Math.random() * 32) : (68 + Math.random() * 26);
      const top = Math.random() * 85 + 5;
      return {
        emoji,
        left: `${left}%`,
        top: `${top}%`,
        fontSize: `${1 + Math.random() * 1.2}rem`,
        driftX: (Math.random() - 0.5) * 35,
        driftY: -30 - Math.random() * 35,
        duration: 4 + Math.random() * 3,
        rotate: (Math.random() - 0.5) * 45,
      };
    });
  }, []);

  /* ── Phase timeline ── */
  useEffect(() => {
    const t1 = setTimeout(() => setPhase('assemble'), 200);
    const t2 = setTimeout(() => setPhase('idle'),     1800);
    const t3 = setTimeout(() => setPhase('exit'),     3600);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, []);

  /* ── Mouse-tracking rotation ── */
  useEffect(() => {
    const onMove = (e) => {
      mouseRef.current = {
        x:  (e.clientX / window.innerWidth  - 0.5) * 28,
        y: -(e.clientY / window.innerHeight - 0.5) * 20,
      };
    };
    window.addEventListener('mousemove', onMove);

    const loop = () => {
      const target = mouseRef.current;
      const cur = currentRot.current;
      cur.x += (target.y - cur.x) * 0.06;
      cur.y += (target.x - cur.y) * 0.06;
      if (groupRef.current) {
        groupRef.current.style.transform =
          `perspective(1400px) rotateX(${cur.x}deg) rotateY(${cur.y}deg)`;
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const isAssembled = phase === 'idle' || phase === 'exit';

  /* ── Per-layer animation ── */
  const layerVariants = (idx) => {
    const parity = idx % 2 === 0;
    const mod3   = idx % 3;
    return {
      intro: {
        opacity: 0,
        scale: 0.3,
        x: parity ? -200 : 200,
        y: mod3 === 0 ? -140 : mod3 === 1 ? 90 : -50,
        rotateX: parity ? 55 : -55,
        rotateZ: (parity ? 1 : -1) * (10 + idx * 2),
      },
      assemble: {
        opacity: idx === LAYERS - 1 ? 1 : Math.max(0.06, 0.45 - idx * 0.12),
        scale: 1,
        x: 0, y: 0,
        rotateX: 0, rotateZ: 0,
        transition: {
          duration: 0.9,
          delay: idx * 0.025,
          ease: [0.22, 1, 0.36, 1],
        },
      },
      idle: {
        opacity: idx === LAYERS - 1 ? 1 : Math.max(0.06, 0.45 - idx * 0.12),
        scale: 1,
        x: 0,
        y: [0, -8, 0],
        rotateX: 0, rotateZ: 0,
        transition: {
          y: { duration: 3, repeat: Infinity, ease: 'easeInOut', delay: idx * 0.012 },
        },
      },
    };
  };

  return (
    <div
      className={`splash-overlay ${phase === 'exit' ? 'splash-overlay--exit' : ''}`}
      onTransitionEnd={(e) => {
        if (e.propertyName === 'opacity' && phase === 'exit') {
          onComplete();
        }
      }}
    >
          {/* Soft radial glow */}
          <div className="splash-spotlight" />

          {/* Subtle grid */}
          <div className="splash-grid" />

          {/* Floating paw-prints, hearts, bones in background */}
          <div className="splash-floaters" aria-hidden>
            {floaters.map((fl, i) => (
              <motion.div
                key={i}
                className="sp-floater"
                style={{
                  left: fl.left,
                  top: fl.top,
                  fontSize: fl.fontSize,
                }}
                animate={{
                  y: [0, fl.driftY, 0],
                  x: [0, fl.driftX, 0],
                  opacity: [0.12, 0.30, 0.12],
                  rotate: [0, fl.rotate, 0],
                }}
                transition={{
                  duration: fl.duration,
                  delay: i * 0.25,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                {fl.emoji}
              </motion.div>
            ))}
          </div>

          {/* ── 3D Logo Stage ── */}
          <div className="splash-stage">
            <div
              className="logo-3d-group"
              ref={groupRef}
              style={{ transformStyle: 'preserve-3d' }}
            >
              {/* Back extrusion layers — tinted silhouette copies */}
              {Array.from({ length: LAYERS }).map((_, idx) => {
                const depth = (LAYERS - 1 - idx) * 6;
                const isFront = idx === LAYERS - 1;
                return (
                  <motion.div
                    key={idx}
                    className={`logo-layer ${isFront ? 'logo-layer--front' : ''}`}
                    style={{
                      transform: `translateZ(${-depth}px)`,
                    }}
                    variants={layerVariants(idx)}
                    initial="intro"
                    animate={phase === 'idle' || phase === 'exit' ? 'idle' : phase}
                  >
                    <img
                      src="/medipaw_logo_svg.svg"
                      alt="MediPaw Logo"
                      className="logo-layer-img"
                      style={{
                        filter: isFront
                          ? 'none'
                          : `brightness(0.92) contrast(1.05)`,
                        opacity: isFront ? 1 : Math.max(0.04, 0.45 - idx * 0.025),
                      }}
                      draggable={false}
                    />
                  </motion.div>
                );
              })}

              {/* Glow halo after assembly */}
              {isAssembled && (
                <motion.div
                  className="logo-halo"
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: [0.25, 0.08, 0.25], scale: [1, 1.2, 1] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                />
              )}

              {/* Orbit rings */}
              {isAssembled && (
                <>
                  <motion.div
                    className="logo-ring ring-teal"
                    initial={{ opacity: 0, rotate: 0 }}
                    animate={{ opacity: 0.3, rotate: 360 }}
                    transition={{ opacity: { duration: 0.5 }, rotate: { duration: 20, repeat: Infinity, ease: 'linear' } }}
                  />
                  <motion.div
                    className="logo-ring ring-coral"
                    initial={{ opacity: 0, rotate: 0 }}
                    animate={{ opacity: 0.2, rotate: -360 }}
                    transition={{ opacity: { duration: 0.5, delay: 0.2 }, rotate: { duration: 26, repeat: Infinity, ease: 'linear' } }}
                  />
                </>
              )}
            </div>
          </div>

          {/* Footer loading */}
          <motion.div
            className="splash-footer"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isAssembled ? 1 : 0, y: isAssembled ? 0 : 20 }}
          >
            <div className="splash-dots">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="sdot"
                  animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
                  transition={{ duration: 1.4, delay: i * 0.22, repeat: Infinity }}
                />
              ))}
            </div>
            <p className="splash-status">Initializing AI Triage Engine</p>
          </motion.div>
    </div>
  );
}
