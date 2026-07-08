import { motion } from 'framer-motion';

export default function OrganicTriageCard({ stat, index, offsetClass, accentStyle }) {
  // Alternate asymmetry: left cards (0,2) vs right cards (1,3)
  const isLeftCard = index === 0 || index === 2;

  return (
    <motion.article
      className={`relative flex flex-col transition-all ${offsetClass}`}
      initial={{ opacity: 0, y: 24, rotateX: 14 }}
      whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -7, scale: 1.018, rotateX: -3, rotateY: isLeftCard ? 1.5 : -1.5, boxShadow: 'none' }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24, delay: index * 0.04 }}
      style={{
        width: '220px',
        flexShrink: 0,
        padding: '24px 28px',
        border: `2px solid ${accentStyle.borderColor}`,
        borderRadius: isLeftCard 
          ? '45% 55% 60% 40% / 55% 45% 55% 45%'
          : '55% 45% 40% 60% / 45% 55% 45% 55%',
        backgroundColor: '#ffffff',
        overflow: 'visible',
        boxShadow: 'none',
        transformStyle: 'preserve-3d',
      }}
    >
      <motion.span
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: '-7px',
          border: `1px solid ${accentStyle.borderColor}`,
          borderRadius: 'inherit',
          opacity: 0.18,
          pointerEvents: 'none',
        }}
        animate={{ scale: [1, 1.035, 1], opacity: [0.12, 0.28, 0.12] }}
        transition={{ duration: 3.2, repeat: Infinity, delay: index * 0.22, ease: 'easeInOut' }}
      />
      <span
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: '10px',
          borderRadius: 'inherit',
          background: `radial-gradient(circle at 30% 10%, ${accentStyle.badgeBg}, transparent 42%)`,
          opacity: 0.56,
          pointerEvents: 'none',
        }}
      />
      {/* Status Badge */}
      <div className="mb-6 relative z-10">
        <span
          className="inline-flex items-center px-2.5 py-1.5 text-xs font-bold uppercase tracking-widest rounded-full"
          style={{
            backgroundColor: accentStyle.badgeBg,
            color: accentStyle.badgeColor,
          }}
        >
          {stat.priority}
        </span>
      </div>

      {/* Content: Count + Label */}
      <div className="flex flex-col gap-3 relative z-10">
        <div className="font-mono text-5xl font-bold text-slate-900 leading-tight tabular-nums" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {stat.count}
        </div>
        <p className="text-xs font-medium leading-snug text-slate-600">
          {stat.label}
        </p>
      </div>
    </motion.article>
  );
}
