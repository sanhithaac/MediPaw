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
      whileHover={{ y: -4, scale: 1.01, rotateX: -3, rotateY: 1, boxShadow: 'none' }}
      transition={{ duration: 0.55, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
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
      {/* Status Badge */}
      <div className="mb-6">
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
      <div className="flex flex-col gap-3">
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
