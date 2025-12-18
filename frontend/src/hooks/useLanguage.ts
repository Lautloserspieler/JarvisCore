import { useCallback } from 'react';
import i18next from 'i18next';

/**
 * Hook für Sprachverwaltung
 * Bietet aktuelle Sprache und Umschaltunssfunktionalität
 */
export const useLanguage = () => {
  // Aktuelle Sprache
  const currentLanguage = i18next.language || localStorage.getItem('jarvis-language') || 'en';

  /**
   * Sprache wechseln
   * @param language - 'de' oder 'en'
   */
  const switchLanguage = useCallback((language: 'de' | 'en') => {
    i18next.changeLanguage(language);
    localStorage.setItem('jarvis-language', language);
    
    // Optional: Seite aktualisieren für sofortige Änderungen
    // window.location.reload();
  }, []);

  /**
   * Zwischen Deutsch und Englisch umschalten
   */
  const toggleLanguage = useCallback(() => {
    const newLanguage = currentLanguage === 'de' ? 'en' : 'de';
    switchLanguage(newLanguage);
  }, [currentLanguage, switchLanguage]);

  /**
   * Verfügbare Sprachen
   */
  const availableLanguages = [
    { code: 'de', name: '🇩🇪 Deutsch' },
    { code: 'en', name: '🇬🇧 English' }
  ];

  return {
    currentLanguage,
    switchLanguage,
    toggleLanguage,
    availableLanguages,
    isGerman: currentLanguage === 'de',
    isEnglish: currentLanguage === 'en'
  };
};
