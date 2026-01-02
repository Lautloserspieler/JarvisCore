# Model Gallery

## Überblick

Die Model Gallery liefert eine kuratierte Liste von LLM-Modellen, die über das Backend geladen, gefiltert und installiert werden können. Sie basiert auf einer JSON-Quelle (lokal oder CDN), wird zwischengespeichert und stellt Download-Fortschritte per WebSocket bereit.

Wichtige Pfade:

- Lokale Gallery-Datei: `config/models_gallery.json`
- Cache-Datei: `cache/gallery_cache.json`
- Installationsziel der Modelle: `models/llm/`
- Registry der installierten Modelle: `config/models.json`

## Installation & Einrichtung

1. **Gallery-Daten bereitstellen**
   - Standardmäßig wird `config/models_gallery.json` verwendet.
   - Optional kann im Code eine CDN-URL an `load_gallery`/`fetch_gallery` übergeben werden, z. B. in einer eigenen Integration oder bei Bedarf für eigene Deployments.

2. **Backend starten**
   - Stelle sicher, dass das Backend läuft und die Routen unter `/api/models` verfügbar sind.
   - Die Gallery wird beim ersten Zugriff geladen und anschließend gecached.

3. **Frontend nutzen**
   - Die Gallery wird im Modelle-Tab (Gallery-Reiter) angezeigt.
   - Filter (Kategorie, Sprache, Rating, Größe) und Suche greifen auf die geladenen Daten zu.

4. **Modelle installieren**
   - Die Installation erfolgt über `POST /api/models/gallery/{model_id}/install`.
   - Fortschritt wird über `ws://<host>/api/models/ws/progress` übertragen.

## Schema-Beschreibung

### Gallery-Payload (`config/models_gallery.json`)

```json
{
  "version": "1.0",
  "generatedAt": "2024-10-01T00:00:00Z",
  "models": [
    {
      "id": "llama-3-2-3b-q4",
      "name": "Llama 3.2 3B Q4",
      "categories": ["chat", "general"],
      "checksum": "sha256:...",
      "downloadUrl": "https://.../model.gguf",
      "languages": ["en", "de"],
      "recommendedHardware": {
        "cpu": "8-core",
        "gpu": "CPU",
        "ramGb": 16,
        "vramGb": 0
      },
      "parameters": "3B",
      "sizeGb": 1.8,
      "rating": 4.2,
      "license": "Meta",
      "description": "Beschreibung...",
      "tags": ["tier-1", "cpu-friendly"],
      "quantization": "Q4",
      "contextLength": 8192,
      "updatedAt": "2024-10-01"
    }
  ]
}
```

**Feldübersicht**

- `version` (string): Versionskennung des Gallery-Schemas.
- `generatedAt` (string, ISO-8601): Zeitpunkt der Gallery-Erstellung.
- `models` (array): Liste der Modelle.

**Model-Felder**

- `id` (string): Eindeutige Modell-ID.
- `name` (string): Anzeigename.
- `categories` (string[]): Kategorien/Tags zur Filterung.
- `checksum` (string): SHA256-Checksumme (inkl. Prefix).
- `downloadUrl` (string/URL): Download-Quelle.
- `languages` (string[]): Unterstützte Sprachen.
- `recommendedHardware` (object): Empfohlene Hardware.
- `parameters` (string): Parametergröße (z. B. `7B`).
- `sizeGb` (number): Modellgröße in GB.
- `rating` (number): Bewertung (0–5).
- `license` (string): Lizenz.
- `description` (string): Kurzbeschreibung.
- `tags` (string[]): Zusätzliche Tags.
- `quantization` (string): Quantisierung (z. B. `Q4_K_M`).
- `contextLength` (number): Kontextlänge in Tokens.
- `updatedAt` (string): Aktualisierungsdatum.

**recommendedHardware**

- `cpu` (string)
- `gpu` (string)
- `ramGb` (number, >= 1)
- `vramGb` (number, >= 0)

### Installierte Modelle (`config/models.json`)

Die Registry speichert installierte Modelle und deren Status.

Beispiel-Eintrag:

```json
{
  "models": {
    "llama-3-2-3b-q4": {
      "id": "llama-3-2-3b-q4",
      "name": "Llama 3.2 3B Q4",
      "path": "models/llm/llama-3-2-3b-q4.gguf",
      "size": 1932735283,
      "installedAt": "2024-10-01T12:34:56+00:00",
      "backend": "gallery",
      "active": false
    }
  }
}
```

Zusätzliche Status-Felder können beim Abruf über `GET /api/models/installed` ergänzt werden:

- `status`: `installed`, `missing` oder `unregistered`

## API-Endpoints

- `GET /api/models/gallery`
  - Liefert die vollständige Gallery-Payload.
- `GET /api/models/gallery/search`
  - Query-Parameter: `query`, `category`, `language`, `min_rating`, `min_size_gb`, `max_size_gb`.
- `POST /api/models/gallery/{model_id}/install`
  - Startet den Download und die Registrierung.
- `GET /api/models/installed`
  - Liefert installierte Modelle inklusive Status.
- `DELETE /api/models/{model_id}`
  - Entfernt Registry-Eintrag und ggf. Datei.
- `WS /api/models/ws/progress`
  - Sendet Fortschritte: `{ "model_id", "progress", "downloaded", "total" }`.

## FAQ

**Wie aktualisiere ich die Gallery?**
- Passe `config/models_gallery.json` an oder lade eine neue Datei über eine CDN-Quelle und aktualisiere den Cache durch einen Neustart oder Cache-Löschung.

**Warum sehe ich keine Modelle?**
- Prüfe, ob `config/models_gallery.json` existiert und gültig ist.
- Stelle sicher, dass der Cache (`cache/gallery_cache.json`) nicht veraltet oder beschädigt ist.

**Warum bleibt der Fortschritt bei 0 %?**
- Stelle sicher, dass das CDN/der Download erreichbar ist und dass der WebSocket `/api/models/ws/progress` offen ist.

**Wie entferne ich ein Modell vollständig?**
- Nutze `DELETE /api/models/{model_id}`; dies entfernt den Registry-Eintrag und löscht die Datei, falls sie vorhanden ist.
