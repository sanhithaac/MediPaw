import { motion } from 'framer-motion';
import './ContactPage.css';

const CONTACT_METHODS = [
  { title: 'Email', value: 'hello@medipaw.ai', detail: 'For product questions and collaborations' },
  { title: 'Phone', value: '+1 (800) 555-0142', detail: 'Mon–Fri • 8am–6pm PST' },
  { title: 'Studio', value: 'Remote • Global', detail: 'We work with clinics, shelters, and labs worldwide' },
];

export default function ContactPage() {
  return (
    <div className="contact-page">
      <motion.section
        className="contact-hero"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="contact-hero-copy">
          <span className="section-label">Contact</span>
          <h1 className="contact-title">
            Let’s build a calmer, faster <span className="gradient-text">care workflow</span>
          </h1>
          <p className="contact-desc">
            Whether you are launching a new clinic experience or refining an existing triage pipeline, we can help shape a product experience that feels precise, human, and premium.
          </p>
          <div className="contact-pill-row">
            <span className="contact-pill">Clinical UI systems</span>
            <span className="contact-pill">Product strategy</span>
            <span className="contact-pill">AI workflow design</span>
          </div>
        </div>

        <motion.div
          className="contact-card contact-card--primary"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
        >
          <p className="contact-card-label">Available for</p>
          <h3>Product design sprints and implementation support</h3>
          <ul>
            <li>Fast-moving veterinary software teams</li>
            <li>Clinical operations and intake systems</li>
            <li>AI-assisted triage and patient journeys</li>
          </ul>
          <motion.button
            className="btn-primary"
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
          >
            Start a conversation
          </motion.button>
        </motion.div>
      </motion.section>

      <motion.section
        className="contact-grid"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, delay: 0.18 }}
      >
        <div className="contact-card contact-card--secondary">
          <p className="contact-card-label">Say hello</p>
          <h3>We respond fast and thoughtfully.</h3>
          <p>
            Share your goals, constraints, and timeline. We will help you turn the idea into a clean and confident experience.
          </p>
        </div>

        <div className="contact-card contact-card--form">
          <div className="contact-form-row">
            <label>
              Name
              <input type="text" placeholder="Your name" />
            </label>
            <label>
              Email
              <input type="email" placeholder="you@company.com" />
            </label>
          </div>

          <label>
            Company
            <input type="text" placeholder="Clinic, shelter, or product team" />
          </label>

          <label>
            What are you building?
            <textarea rows="5" placeholder="Tell us about the experience you want to create." />
          </label>

          <button className="btn-outline">Send message</button>
        </div>
      </motion.section>

      <motion.section
        className="contact-methods"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, delay: 0.24 }}
      >
        {CONTACT_METHODS.map((item) => (
          <div key={item.title} className="contact-method-card">
            <p className="contact-method-title">{item.title}</p>
            <h4>{item.value}</h4>
            <p>{item.detail}</p>
          </div>
        ))}
      </motion.section>
    </div>
  );
}
