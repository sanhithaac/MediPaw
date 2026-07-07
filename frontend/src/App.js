import React, { useState, lazy, Suspense, startTransition } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';
import Navbar from './components/Navbar';
import Logo3DSplash from './components/Logo3DSplash';
import './App.css';

// Lazy load heavy components to prevent blocking the animation thread
const Background3D = lazy(() => import('./components/Background3D'));
const Dashboard    = lazy(() => import('./pages/Dashboard'));
const IntakePage   = lazy(() => import('./pages/IntakePage'));
const ResultsPage  = lazy(() => import('./pages/ResultsPage'));const ContactPage  = lazy(() => import('./pages/ContactPage'));
function App() {
  const [splashDone, setSplashDone] = useState(false);

  return (
    <BrowserRouter>
      <div className="app-root">
        {/* 3D Logo splash — shown on first load */}
        <AnimatePresence mode="wait">
          {!splashDone && (
            <Logo3DSplash
              key="splash"
              onComplete={() => {
                // Use requestAnimationFrame and startTransition to defer mounting of heavy pages
                requestAnimationFrame(() => {
                  setTimeout(() => {
                    startTransition(() => {
                      setSplashDone(true);
                    });
                  }, 80); // Thread clearance buffer
                });
              }}
            />
          )}
        </AnimatePresence>

        {/* Main app shell — deferred rendering after splash unmount */}
        {splashDone && (
          <Suspense fallback={
            <div className="deferred-loader">
              <div className="deferred-spinner" />
              <p>Loading Triage Center...</p>
            </div>
          }>
            <Background3D />
            <Navbar />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/intake" element={<IntakePage />} />
                <Route path="/results/:caseId" element={<ResultsPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </Suspense>
        )}

        {/* Toast notifications */}
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: 'rgba(13, 17, 23, 0.96)',
              border: '1px solid rgba(255,255,255,0.10)',
              color: '#f0f4f8',
              backdropFilter: 'blur(24px)',
              fontFamily: 'Inter, sans-serif',
              fontSize: '0.88rem',
            },
            success: {
              iconTheme: { primary: '#1a9e8b', secondary: '#fff' },
            },
            error: {
              iconTheme: { primary: '#ef4444', secondary: '#fff' },
            },
          }}
        />
      </div>
    </BrowserRouter>
  );
}

export default App;
