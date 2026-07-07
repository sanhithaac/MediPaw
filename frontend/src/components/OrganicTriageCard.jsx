import { motion } from 'framer-motion';

export default function OrganicTriageCard({ stat, index, offsetClass, accentStyle }) {
  // Alternate asymmetry: left cards (0,2) vs right cards (1,3)
  const isLeftCard = index === 0 || index === 2;

  return (
    <motion.article
      className={`relative flex flex-col bg-white transition-all hover:shadow-md ${offsetClass}`}
      initial={{ opacity: 0, y: 24, rotateX: 14 }}
      whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      whileHover={{ y: -6, scale: 1.02, rotateX: -4, rotateY: 2, boxShadow: '0 18px 32px rgba(15, 23, 42, 0.10)' }}
      transition={{ duration: 0.55, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
      style={{
        width: '220px',
        flexShrink: 0,
        padding: '24px 28px',
        borderLeft: `4px solid ${accentStyle.borderColor}`,
        borderTop: `1px solid ${accentStyle.borderColor}22`,
        borderRight: `1px solid ${accentStyle.borderColor}22`,
        borderBottom: `1px solid ${accentStyle.borderColor}22`,
        borderRadius: isLeftCard 
          ? '45% 55% 60% 40% / 55% 45% 55% 45%'
          : '55% 45% 40% 60% / 45% 55% 45% 55%',
        backgroundColor: '#ffffff',
        overflow: 'visible',
        boxShadow: '0 10px 24px rgba(15, 23, 42, 0.06), 0 2px 8px rgba(15, 23, 42, 0.03)',
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
        <div className="font-mono text-5xl font-bold text-slate-900 leading-tight">
          {stat.count}
        </div>
        <p className="text-xs font-medium leading-snug text-slate-600">
          {stat.label}
        </p>
      </div>
    </motion.article>
  );
}
