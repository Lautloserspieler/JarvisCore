# Zu JarvisCore beitragen

Zunächst einmal: Vielen Dank, dass du daran interessiert bist, zu JarvisCore beizutragen! 🎉 Menschen wie du machen JarvisCore zu einem großartigen Tool.

## Inhaltsverzeichnis

- [Verhaltenskodex](#verhaltenskodex)
- [Erste Schritte](#erste-schritte)
- [Wie kann ich beitragen?](#wie-kann-ich-beitragen)
- [Entwicklungsumgebung](#entwicklungsumgebung)
- [Pull-Request-Prozess](#pull-request-prozess)
- [Coding-Standards](#coding-standards)
- [Commit-Messages](#commit-messages)
- [Testing](#testing)
- [Dokumentation](#dokumentation)

## Verhaltenskodex

Dieses Projekt und alle daran Beteiligten unterliegen unserem [Verhaltenskodex](CODE_OF_CONDUCT.md). Durch deine Teilnahme verpflichtest du dich, diesen Kodex einzuhalten. Bitte melde inakzeptables Verhalten an [KONTAKT-EMAIL EINFÜGEN].

## Erste Schritte

### Voraussetzungen

- Python 3.11+
- Go 1.21+
- Node.js 18+ und npm
- Docker und Docker Compose
- Git

### Fork & Clone

1. Forke das Repository auf GitHub
2. Clone deinen Fork lokal:
   ```bash
   git clone https://github.com/DEIN_BENUTZERNAME/JarvisCore.git
   cd JarvisCore
   ```
3. Füge das Upstream-Repository hinzu:
   ```bash
   git remote add upstream https://github.com/Lautloserspieler/JarvisCore.git
   ```

## Wie kann ich beitragen?

### Fehler melden

Bevor du einen Fehlerbericht erstellst, prüfe bitte bestehende Issues, um Duplikate zu vermeiden. Beim Erstellen eines Fehlerberichts füge bitte folgendes ein:

- **Klaren Titel und Beschreibung**
- **Schritte zur Reproduktion** des Problems
- **Erwartetes Verhalten** vs **tatsächliches Verhalten**
- **Screenshots** falls zutreffend
- **Umgebungsdetails** (Betriebssystem, Python-Version, Docker-Version, etc.)
- **Relevante Logs** aus dem `logs/` Verzeichnis

### Verbesserungen vorschlagen

Verbesserungsvorschläge werden als GitHub Issues verfolgt. Beim Erstellen eines Verbesserungsvorschlags:

- **Verwende einen klaren und beschreibenden Titel**
- **Gib eine detaillierte Beschreibung** der vorgeschlagenen Verbesserung
- **Erkläre, warum diese Verbesserung nützlich wäre**
- **Liste Alternativen auf**, die du in Betracht gezogen hast

### Dein erster Code-Beitrag

Unsicher, wo du anfangen sollst? Suche nach Issues mit folgenden Labels:

- `good first issue` - Gut für Neulinge
- `help wanted` - Zusätzliche Aufmerksamkeit erforderlich
- `documentation` - Verbesserungen oder Ergänzungen zur Dokumentation

### Pull Requests

Pull Requests sind der beste Weg, um Änderungen vorzuschlagen. Wir heißen deine Pull Requests aktiv willkommen:

1. Forke das Repo und erstelle deinen Branch von `main`
2. Mache deine Änderungen
3. Füge Tests hinzu, falls zutreffend
4. Stelle sicher, dass alle Tests bestehen
5. Aktualisiere die Dokumentation
6. Reiche einen Pull Request ein

## Entwicklungsumgebung

### Lokale Entwicklung (Docker)

```bash
# Repository klonen
git clone https://github.com/DEIN_BENUTZERNAME/JarvisCore.git
cd JarvisCore

# Alle Services starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

### Lokale Entwicklung (Nativ)

#### Backend (Python)

```bash
cd backend

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren (empfohlen)
cd ..
pip install -e ".[dev,ci]"
cd backend

# Legacy (wird entfernt)
# pip install -r requirements.txt

# Backend starten
python main.py
```

#### Frontend (Vue 3)

```bash
cd frontend

# Abhängigkeiten installieren
npm install

# Development-Server starten
npm run dev
```

#### Go Services

```bash
cd go-services/gateway

# Abhängigkeiten installieren
go mod download

# Service starten
go run cmd/gateway/main.go
```

## Pull-Request-Prozess

### 1. Branch erstellen

```bash
git checkout -b feature/dein-feature-name
# oder
git checkout -b fix/dein-bug-fix
```

Branch-Namenskonventionen:
- `feature/` - Neue Features
- `fix/` - Bugfixes
- `docs/` - Dokumentationsänderungen
- `refactor/` - Code-Refactoring
- `test/` - Tests hinzufügen
- `chore/` - Wartungsaufgaben

### 2. Änderungen vornehmen

- Folge den [Coding-Standards](#coding-standards)
- Schreibe aussagekräftige Commit-Messages
- Halte Commits atomar und fokussiert
- Füge Tests für neue Features hinzu

### 3. Änderungen testen

```bash
# Python-Tests ausführen
cd backend
pytest tests/

# Go-Tests ausführen
cd go-services/gateway
go test ./...

# Frontend-Tests ausführen
cd frontend
npm run test

# Integrationstests ausführen
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 4. Dokumentation aktualisieren

- Relevante README-Abschnitte aktualisieren
- Code-Kommentare hinzufügen/aktualisieren
- API-Dokumentation aktualisieren, falls zutreffend
- Einträge zu CHANGELOG.md hinzufügen

### 5. Pull Request einreichen

```bash
# Branch pushen
git push origin feature/dein-feature-name
```

Erstelle dann einen Pull Request auf GitHub mit:

- Klarem Titel, der die Änderung beschreibt
- Detaillierter Beschreibung von Was und Warum
- Link zu verwandten Issues
- Screenshots/GIFs bei UI-Änderungen
- Checkliste der abgeschlossenen Aufgaben

### 6. Code-Review

- Bearbeite Review-Kommentare
- Halte Diskussionen fokussiert und professionell
- Aktualisiere deinen PR basierend auf Feedback
- Fordere Re-Review an, wenn bereit

## Coding-Standards

### Python (Backend)

- Folge dem [PEP 8](https://pep8.org/) Style Guide
- Nutze [Black](https://black.readthedocs.io/) für Formatierung
- Verwende Type Hints wo angemessen
- Maximale Zeilenlänge: 88 Zeichen
- Verwende aussagekräftige Variablennamen

```python
# Gut
def process_user_input(user_message: str) -> dict:
    """Verarbeite Benutzernachricht und gebe Antwort zurück."""
    return {"response": processed_message}

# Schlecht
def p(m):
    return {"r": m}
```

### Go (Services)

- Folge den [Effective Go](https://golang.org/doc/effective_go) Richtlinien
- Nutze `gofmt` für Formatierung
- Verwende aussagekräftige Package-Namen
- Schreibe godoc-Kommentare für öffentliche Funktionen

```go
// Gut
// ProcessMessage behandelt eingehende Nachricht und gibt Antwort zurück
func ProcessMessage(msg string) (string, error) {
    // ...
}

// Schlecht
func p(m string) string {
    // ...
}
```

### TypeScript/Vue (Frontend)

- Folge Vue 3 Composition API Best Practices
- Nutze TypeScript für Type Safety
- Verwende bereitgestellte ESLint-Konfiguration
- Komponenten-Namen in PascalCase
- Props-Validierung erforderlich

```typescript
// Gut
interface Props {
  userId: string
  userName: string
}

const props = defineProps<Props>()

// Schlecht
const props = defineProps({
  id: String,
  name: String
})
```

### Allgemeine Richtlinien

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- Schreibe selbstdokumentierenden Code
- Kommentiere komplexe Logik
- Vermeide vorzeitige Optimierung

## Commit-Messages

Wir folgen [Conventional Commits](https://www.conventionalcommits.org/):

```
<typ>(<bereich>): <betreff>

<body>

<footer>
```

### Typen

- `feat`: Neues Feature
- `fix`: Bugfix
- `docs`: Dokumentationsänderungen
- `style`: Code-Style-Änderungen (Formatierung, etc.)
- `refactor`: Code-Refactoring
- `test`: Tests hinzufügen oder aktualisieren
- `chore`: Wartungsaufgaben
- `perf`: Performance-Verbesserungen
- `ci`: CI/CD-Änderungen

### Beispiele

```bash
# Gut
feat(backend): Benutzer-Authentifizierungssystem hinzugefügt
fix(frontend): Chat-Input-Fokusproblem behoben
docs(readme): Installationsanleitung aktualisiert

# Schlecht
update
fixed bug
added stuff
```

## Testing

### Tests schreiben

- Schreibe Tests für alle neuen Features
- Halte Test-Coverage über 80%
- Teste Randfälle und Fehlerbedingungen
- Verwende beschreibende Testnamen

### Test-Struktur

```python
# Python (pytest)
def test_user_authentication_success():
    """Teste erfolgreiche Benutzer-Authentifizierung."""
    result = authenticate_user("valid_token")
    assert result.is_authenticated
    assert result.user_id is not None

def test_user_authentication_invalid_token():
    """Teste Authentifizierung mit ungültigem Token."""
    with pytest.raises(AuthenticationError):
        authenticate_user("invalid_token")
```

```go
// Go
func TestProcessMessage(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    string
        wantErr bool
    }{
        {"valid input", "hallo", "verarbeitet", false},
        {"empty input", "", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ProcessMessage(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ProcessMessage() error = %v, wantErr %v", err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("ProcessMessage() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

## Dokumentation

### Code-Dokumentation

- Dokumentiere alle öffentlichen APIs
- Nutze Docstrings für Python-Funktionen/Klassen
- Nutze godoc-Kommentare für Go-Funktionen
- Nutze JSDoc für TypeScript/JavaScript

### Benutzerdokumentation

- Aktualisiere README.md für benutzerseitige Änderungen
- Füge Beispiele für neue Features hinzu
- Halte Installationsanleitungen aktuell
- Aktualisiere Troubleshooting-Guide

### API-Dokumentation

- Dokumentiere alle Endpunkte
- Füge Request/Response-Beispiele hinzu
- Spezifiziere erforderliche/optionale Parameter
- Dokumentiere Fehlercodes

## Hilfe bekommen

Wenn du Hilfe brauchst, kannst du:

- Unsere [Dokumentation](docs/) prüfen
- In [GitHub Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions) fragen
- Unserem [Discord Server](#) beitreten (kommt bald)
- Uns eine E-Mail an [KONTAKT-EMAIL EINFÜGEN] senden

## Anerkennung

Contributors werden:

- In [CONTRIBUTORS.md](CONTRIBUTORS.md) aufgelistet
- In Release-Notes erwähnt
- In unserem README anerkannt
- Mit speziellen Rollen in Community-Spaces ausgezeichnet

## Lizenz

Durch deine Beiträge stimmst du zu, dass deine Beiträge unter der [Apache License 2.0](LICENSE) lizenziert werden.

---

**Vielen Dank für deinen Beitrag zu JarvisCore!** 🚀
