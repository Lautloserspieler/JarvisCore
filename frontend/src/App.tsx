import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { Toaster } from '@/components/ui/toaster';

// Lazy loaded pages
const ChatPage = React.lazy(() => import('@/pages/ChatPage'));
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'));
const MemoryPage = React.lazy(() => import('@/pages/MemoryPage'));
const ModelsPage = React.lazy(() => import('@/pages/ModelsPage'));
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'));
const NotFound = React.lazy(() => import('@/pages/NotFound'));

// Navigation Component
const Navigation: React.FC = () => {
  const { t } = require('react-i18next').useTranslation();
  const location = require('react-router-dom').useLocation();
  const navigate = require('react-router-dom').useNavigate();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: t('navigation.chat'), icon: '💬' },
    { path: '/dashboard', label: t('navigation.dashboard'), icon: '📊' },
    { path: '/memory', label: t('navigation.memory'), icon: '🧠' },
    { path: '/models', label: t('navigation.models'), icon: '🤖' },
    { path: '/settings', label: t('navigation.settings'), icon: '⚙️' }
  ];

  return (
    <nav className="flex gap-2 mb-6 border-b pb-2 overflow-x-auto">
      {navItems.map(item => (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
            isActive(item.path)
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-accent'
          }`}
        >
          {item.icon} {item.label}
        </button>
      ))}
    </nav>
  );
};

// Loading Fallback
const LoadingFallback: React.FC = () => {
  const { t } = require('react-i18next').useTranslation();
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin text-4xl mb-4">⚙️</div>
        <p className="text-muted-foreground">{t('common.loading')}</p>
      </div>
    </div>
  );
};

// Main App Component
const AppContent: React.FC = () => {
  const { i18n } = require('react-i18next').useTranslation();

  // Handle language changes
  useEffect(() => {
    const handleLanguageChanged = (lng: string) => {
      document.documentElement.lang = lng;
      document.documentElement.dir = lng === 'ar' ? 'rtl' : 'ltr';
    };

    i18n.on('languageChanged', handleLanguageChanged);
    
    // Set initial language
    handleLanguageChanged(i18n.language);

    return () => {
      i18n.off('languageChanged', handleLanguageChanged);
    };
  }, [i18n]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto p-4">
        <Navigation />
        <main className="py-4">
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/memory" element={<MemoryPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/not-found" element={<NotFound />} />
              <Route path="*" element={<Navigate to="/not-found" />} />
            </Routes>
          </Suspense>
        </main>
      </div>
      <Toaster />
    </div>
  );
};

// Main App with i18n Provider
const App: React.FC = () => {
  return (
    <I18nextProvider i18n={i18n}>
      <Router>
        <AppContent />
      </Router>
    </I18nextProvider>
  );
};

export default App;
