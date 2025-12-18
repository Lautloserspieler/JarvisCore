import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import de from './locales/de.json';
import en from './locales/en.json';

// Browser language detection
const browserLanguage = navigator.language.split('-')[0];
const defaultLanguage = ['de', 'en'].includes(browserLanguage) ? browserLanguage : 'en';

// Saved preference from localStorage
const savedLanguage = localStorage.getItem('jarvis-language') || defaultLanguage;

i18next
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: de },
      en: { translation: en }
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false // React protects from XSS
    },
    react: {
      useSuspense: false // Disable suspense for now
    }
  });

// Save language preference on change
i18next.on('languageChanged', (lng) => {
  localStorage.setItem('jarvis-language', lng);
});

export default i18next;