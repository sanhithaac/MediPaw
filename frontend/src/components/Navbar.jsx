import { useEffect, useRef } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './Navbar.css';

/* ── Mini 3D Logo using actual image ── */
function MiniLogo() {
  const groupRef = useRef(null);
  const mouse    = useRef({ x: 0, y: 0 });
  const cur      = useRef({ x: 0, y: 0 });
  const raf      = useRef(null);

  useEffect(() => {
    const el = groupRef.current;
    if (!el) return;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      mouse.current.x = ((e.clientX - r.left) / r.width  - 0.5) * 22;
      mouse.current.y = -((e.clientY - r.top)  / r.height - 0.5) * 16;
    };
    const onLeave = () => { mouse.current = { x: 0, y: 0 }; };
    el.addEventListener('mousemove', onMove);
    el.addEventListener('mouseleave', onLeave);

    const loop = () => {
      cur.current.x += (mouse.current.y - cur.current.x) * 0.08;
      cur.current.y += (mouse.current.x - cur.current.y) * 0.08;
      if (el) el.style.transform =
        `perspective(600px) rotateX(${cur.current.x}deg) rotateY(${cur.current.y}deg)`;
      raf.current = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      el.removeEventListener('mousemove', onMove);
      el.removeEventListener('mouseleave', onLeave);
      cancelAnimationFrame(raf.current);
    };
  }, []);

  return (
    <div className="mini-logo-wrapper" ref={groupRef} style={{ transformStyle: 'preserve-3d' }}>
      {/* Extrusion shadow layers (5 behind) */}
      {[4, 3, 2, 1, 0].map(d => (
        <img
          key={d}
          src="/medipaw_logo_svg.svg"
          alt=""
          className="mini-logo-layer"
          style={{
            transform: `translateZ(${-d * 1.5}px)`,
            filter: d === 0 ? 'none' : `brightness(0.92) contrast(1.05)`,
            opacity: d === 0 ? 1 : Math.max(0.06, 0.3 - d * 0.05),
          }}
          draggable={false}
        />
      ))}
    </div>
  );
}

const NAV_LINKS = [
  { to: '/',        label: 'Dashboard' },
  { to: '/intake',  label: 'New Case'  },
  { to: '/contact', label: 'Contact'   },
];

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <motion.nav
      className="navbar"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="navbar-inner">
        {/* Logo */}
        <button className="navbar-logo-btn" onClick={() => navigate('/')}>
          <MiniLogo />
        </button>

        {/* Nav links */}
        <div className="navbar-links">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>

        {/* Right CTA */}
        <motion.button
          className="btn-primary navbar-cta"
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => navigate('/intake')}
        >
          <span>＋</span> New Intake
        </motion.button>
      </div>
    </motion.nav>
  );
}
