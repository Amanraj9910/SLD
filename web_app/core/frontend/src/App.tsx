import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import bot animations
import './styles/bot-animations.css';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import DebugPanel from './components/DebugPanel';
import SLDBot from './components/SLDBot';

// Context
import { SLDProvider, useSLD } from './contexts/SLDContext';

// Pages
import HomePage from './pages/HomePage';
import ComponentDetectionPage from './pages/ComponentDetectionPage';
import InteractiveVisualizationPage from './pages/InteractiveVisualizationPage';
import TextDetectionPage from './pages/TextDetectionPage';
import AnnotationToolPage from './pages/AnnotationToolPage';
import AboutPage from './pages/AboutPage';
// import BotDemo from './components/bot/BotDemo';

// Styles
import './index.css';

// Main App Content Component
const AppContent: React.FC = () => {
  const { sldData } = useSLD();

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Navigation */}
      <Navbar />

      {/* Main Content */}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/component-detection" element={<ComponentDetectionPage />} />
          <Route path="/interactive-visualization" element={<InteractiveVisualizationPage />} />
          <Route path="/text-detection" element={<TextDetectionPage />} />
          <Route path="/annotation-tool" element={<AnnotationToolPage />} />
          {/* <Route path="/bot-demo" element={<BotDemo />} /> */}
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <Footer />

      {/* Debug Panel (temporary) */}
      <DebugPanel />

      {/* SLD Bot - Global assistant available on all pages */}
      <SLDBot
        sldData={sldData}
        isVisible={true}
      />

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#ffffff',
            color: '#374151',
            border: '1px solid #e5e7eb',
            borderRadius: '0.75rem',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
          },
          success: {
            iconTheme: {
              primary: '#E21C15',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#dc2626',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <SLDProvider>
      <Router>
        <AppContent />
      </Router>
    </SLDProvider>
  );
};

export default App;
