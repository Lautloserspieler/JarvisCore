import { useState } from 'react';
import { X, Lock, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';

interface TokenDialogProps {
  modelName: string;
  language: 'de' | 'en';
  onClose: () => void;
  onSubmit: (data: { token: string, remember: boolean }) => void;
}

const translations = {
  de: {
    title: 'HuggingFace Token benötigt',
    message: 'Dieses Modell benötigt einen HuggingFace Token für den Download.',
    getToken: 'Token erstellen',
    tokenLabel: 'HuggingFace Token',
    tokenPlaceholder: 'hf_...',
    rememberToken: 'Token für zukünftige Downloads speichern',
    cancel: 'Abbrechen',
    submit: 'Speichern & Download',
    invalidToken: 'Ungültiges Token-Format. Token sollte mit "hf_" beginnen.'
  },
  en: {
    title: 'HuggingFace Token Required',
    message: 'This model requires a HuggingFace token for download.',
    getToken: 'Get Token',
    tokenLabel: 'HuggingFace Token',
    tokenPlaceholder: 'hf_...',
    rememberToken: 'Remember token for future downloads',
    cancel: 'Cancel',
    submit: 'Save & Download',
    invalidToken: 'Invalid token format. Token should start with "hf_"'
  }
};

const TokenDialog = ({ modelName, language, onClose, onSubmit }: TokenDialogProps) => {
  const [token, setToken] = useState('');
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');

  const t = translations[language];

  const handleSubmit = () => {
    setError('');
    
    if (!token) {
      return;
    }
    
    // Validate token format
    if (!token.startsWith('hf_')) {
      setError(t.invalidToken);
      return;
    }
    
    onSubmit({ token, remember });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="relative bg-background border border-border rounded-lg shadow-2xl w-[90%] max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold">{t.title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Info Box */}
          <div className="flex gap-3 p-4 bg-blue-500/10 border-l-4 border-blue-500 rounded-r">
            <Lock className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <p className="text-sm">{t.message}</p>
              <a
                href="https://huggingface.co/settings/tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-500 hover:text-blue-600 font-medium"
              >
                {t.getToken}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Token Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">{t.tokenLabel}</label>
            <Input
              type="password"
              placeholder={t.tokenPlaceholder}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              onKeyPress={handleKeyPress}
              className="font-mono"
            />
            {error && (
              <p className="text-xs text-destructive">{error}</p>
            )}
          </div>

          {/* Remember Checkbox */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="remember"
              checked={remember}
              onCheckedChange={(checked) => setRemember(checked as boolean)}
            />
            <label
              htmlFor="remember"
              className="text-sm cursor-pointer select-none"
            >
              {t.rememberToken}
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 p-6 border-t border-border">
          <Button
            variant="outline"
            onClick={onClose}
          >
            {t.cancel}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!token}
          >
            {t.submit}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TokenDialog;
