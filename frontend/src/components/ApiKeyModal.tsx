import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ExternalLink, Key } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ApiKeyInfo {
  api_key_name: string;
  api_key_label: string;
  api_key_url: string;
  api_key_description: string;
}

interface ApiKeyModalProps {
  open: boolean;
  onClose: () => void;
  apiKeyInfo: ApiKeyInfo;
  onSuccess: () => void;
}

const ApiKeyModal = ({ open, onClose, apiKeyInfo, onSuccess }: ApiKeyModalProps) => {
  const { toast } = useToast();
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!apiKey.trim()) {
      toast({
        title: "Fehler",
        description: "Bitte geben Sie einen API-Key ein",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);

    try {
      // Save API key to backend
      const response = await fetch("http://localhost:5050/api/settings/plugin-api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          [apiKeyInfo.api_key_name]: apiKey.trim(),
        }),
      });

      if (response.ok) {
        toast({
          title: "✅ Gespeichert",
          description: "API-Key wurde erfolgreich gespeichert",
        });
        setApiKey("");
        onSuccess();
        onClose();
      } else {
        throw new Error("API-Key konnte nicht gespeichert werden");
      }
    } catch (error) {
      console.error("Fehler beim Speichern des API-Keys:", error);
      toast({
        title: "Fehler",
        description: "API-Key konnte nicht gespeichert werden",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] holo-card">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API-Key erforderlich
          </DialogTitle>
          <DialogDescription>
            Dieses Plugin benötigt einen API-Key um zu funktionieren.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* API Key Info */}
          <div className="space-y-2 p-4 rounded-lg bg-muted/50">
            <h4 className="font-semibold text-sm">{apiKeyInfo.api_key_label}</h4>
            <p className="text-sm text-muted-foreground">
              {apiKeyInfo.api_key_description}
            </p>
            <a
              href={apiKeyInfo.api_key_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Hier kostenlos registrieren
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {/* API Key Input */}
          <div className="space-y-2">
            <Label htmlFor="api-key">API-Key</Label>
            <Input
              id="api-key"
              type="password"
              placeholder="Geben Sie Ihren API-Key ein"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSave();
                }
              }}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Abbrechen
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Speichert..." : "Speichern"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ApiKeyModal;
