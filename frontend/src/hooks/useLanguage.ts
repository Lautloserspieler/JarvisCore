import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

export const useLanguage = () => {
  const { i18n } = useTranslation();

  const currentLanguage = i18n.language as 'de' | 'en';

  const switchLanguage = useCallback((lang: 'de' | 'en') => {
    i18n.changeLanguage(lang);
  }, [i18n]);

  const toggleLanguage = useCallback(() => {
    const newLang = currentLanguage === 'de' ? 'en' : 'de';
    switchLanguage(newLang);
  }, [currentLanguage, switchLanguage]);

  return {
    currentLanguage,
    switchLanguage,
    toggleLanguage,
    isDE: currentLanguage === 'de',
    isEN: currentLanguage === 'en'
  };
};
