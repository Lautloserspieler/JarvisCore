import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import Index from './pages/Index.tsx';
import { Toaster } from '@/components/ui/toaster';
import './index.css';
import i18n from './i18n';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <BrowserRouter>
        <Index />
        <Toaster />
      </BrowserRouter>
    </I18nextProvider>
  </StrictMode>
);
