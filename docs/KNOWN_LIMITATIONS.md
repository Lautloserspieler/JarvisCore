# Known Limitations (v1.0.0)

**Last Updated:** 2025-12-05  
**Version:** v1.0.0  
**Status:** 🟡 Documented & Planned

> **Diese Punkte sind bekannt und werden in kommenden Updates adressiert.**

---

## 🔒 **Security**

### 1. Token-System ist rudimentär

**Status:** 🟡 PARTIAL - Config-System vorhanden, Implementierung ausständig

**Problem:**
- Desktop-Backend generiert zufälligen Token bei jedem Start
- Keine persistente Speicherung zwischen Sessions
- Keine Token-Rotation oder Ablauf-Mechanismus
- Kein Token-Pairing-Flow im UI

**Auswirkung:**
- Token ändert sich bei jedem Backend-Neustart
- User muss Token manuell synchronisieren
- Keine Token-Verwaltung für mehrere Clients

**Dateien betroffen:**
- `desktop/backend/internal/bridge/jarviscore.go`
- `desktop/config.json` (vorbereitet, nicht verwendet)

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.0.1** | Token aus `config.json` laden/speichern | 1 Tag |
| **v1.1.0** | Token-Pairing UI (QR-Code/Manual Entry) | 2-3 Tage |
| **v1.2.0** | Token-Rotation & Ablauf (JWT) | 3-4 Tage |

**Workaround (aktuell):**
```bash
# Token aus Backend-Log kopieren:
# "Generated API Token: abc123..."
# Dann im Desktop UI manuell eingeben (Settings View)
```

---

### 2. Shell-Command-Injection-Risiken

**Status:** 🟠 ANALYZED - Risiko niedrig, aber Refactoring nötig

**Problem:**
- `core/system_control.py` nutzt `shell=True` an ~4 Stellen
- Potenzielle Injection-Vektoren wenn User-Input direkt verwendet wird

**Aktuelle Findings:**
```python
# Line ~680: Network adapter control (Windows)
subprocess.run(cmd, shell=True, capture_output=True, text=True)

# Line ~904: File attribute commands
subprocess.run(cmd, capture_output=True, text=True)

# Line ~1520: Program launching
subprocess.Popen(program_cmd, shell=True, ...)

# Line ~1539: Windows startfile
os.startfile(path_str)  # Indirekt shell-like
```

**Aktuelle Mitigationen:**
- ✅ Commands aus Whitelist (`program_paths` Dictionary)
- ✅ Pfade durch `SecurityManager` validiert
- ✅ `ensure_command_allowed()` prüft Capabilities
- ✅ Kein direkter User-Input-to-Shell-Pipeline

**Risiko-Einschätzung:**
- **Likelihood:** LOW (nur lokaler Zugriff, Whitelist, Validation)
- **Impact:** CRITICAL (wenn exploitiert)
- **Overall Risk:** 🟡 MEDIUM

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.0.1** | User-Input-Flow-Audit + Logging | 1 Tag |
| **v1.1.0** | Alle `shell=True` → `shell=False` | 2-3 Tage |
| **v1.1.0** | `SafeShell` Wrapper-Klasse | 1 Tag |
| **v1.2.0** | Command-Execution Audit Log | 2 Tage |

**Siehe:** `docs/SECURITY_AUDIT.md` für Details

---

## 🏛️ **Code Quality**

### 3. `system_control.py` ist zu groß (~1600 Zeilen)

**Status:** 🟡 DOCUMENTED - Refactoring-Plan vorhanden

**Problem:**
- Single Responsibility Principle verletzt
- Mischt 7+ verschiedene Concerns:
  - Prozess-Management (Start/Stop/List)
  - Dateisystem-Operationen (Read/Write/Delete)
  - Netzwerk-Adapter-Steuerung
  - Power-Management (Shutdown/Reboot/Lock)
  - Shell-Command-Execution
  - Safe-Mode-Funktionen
  - Windows-Shortcut-Indexierung

**Auswirkung:**
- Schwer wartbar (lange Datei)
- Schwer testbar (viele Dependencies)
- Änderungen riskant (Seiteneffekte)

**Neue Struktur (geplant):**
```
core/system/
├── __init__.py           # Public API
├── base.py              # SystemControl Base Class
├── processes.py         # Programme starten/killen
├── files.py             # Dateisystem-Operationen
├── network.py           # Netzwerk-Adapter
├── power.py             # Shutdown/Reboot/Lock
├── shell.py             # Shell-Befehle (EXTRA SECURE!)
├── metrics.py           # System-Metriken
├── safe_mode.py         # Safe-Mode-Funktionen
└── windows_shortcuts.py  # Windows-specific
```

**Migration-Strategie:**
1. Tests für aktuelle Funktionalität schreiben
2. Modul-by-Modul extrahieren
3. Integration-Tests laufen lassen
4. Legacy-Code entfernen

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.1.0** | Modul-Split (7 Module) | 3-4 Tage |
| **v1.1.0** | Unit-Tests pro Modul | 2 Tage |
| **v1.2.0** | Integration-Tests | 2 Tage |

**Siehe:** `docs/REFACTORING_ROADMAP.md` für Details

---

### 4. TTS-Code ist fragmentiert

**Status:** 🟡 DOCUMENTED - Konsolidierungs-Plan vorhanden

**Problem:**
- 5 verschiedene TTS-Implementierungen parallel:
  ```
  core/
  ├── text_to_speech.py      # Legacy (pyttsx3)
  ├── reliable_tts.py        # Queue-based (pyttsx3)
  ├── xtts_tts.py            # XTTS v1
  ├── xtts_tts_fixed.py      # XTTS v1 Fix
  ├── xttsv2_tts.py          # XTTS v2 ✅ AKTUELL
  └── xttsv2_clone.py        # Voice Cloning ✅ AKTUELL
  ```

**Auswirkung:**
- Verwirrend für neue Entwickler
- Doppelte Logik
- Maintenance-Overhead

**Neue Struktur (geplant):**
```
core/tts/
├── __init__.py           # Public API
├── base.py              # ITTSProvider Interface
├── xtts_v2.py           # XTTS v2 Implementation ✅
├── voice_cloning.py     # Voice Cloning ✅
└── legacy/              # Alte Implementierungen (deprecated)
    ├── text_to_speech.py
    ├── reliable_tts.py
    ├── xtts_tts.py
    └── xtts_tts_fixed.py
```

**Interface (geplant):**
```python
from abc import ABC, abstractmethod

class ITTSProvider(ABC):
    @abstractmethod
    def speak(self, text: str, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def speak_async(self, text: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        pass
```

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.1.0** | ITTSProvider Interface | 1 Tag |
| **v1.1.0** | Legacy-Code zu `legacy/` verschieben | 1 Tag |
| **v1.2.0** | XTTS UI Integration | 2-3 Tage |

---

### 5. Exception Handling unvollständig

**Status:** 🟠 PARTIAL FIX - Mehrere Stellen bereits gefixt

**Problem:**
- Einige `bare except:` Blöcke ohne Logging
- Fehler werden "geschluckt" ohne Trace
- Debugging erschwert

**Bereits gefixt (v1.0.0):**
- ✅ `main.py` - Alle Exceptions geloggt
- ✅ `llm_manager.py` - Spezifische Exception-Typen
- ✅ `security_manager.py` - Fehler-Logging hinzugefügt

**Noch zu fixen:**
- ⚠️ `system_control.py` - Einige bare excepts
- ⚠️ Plugin-System - Fehlerbehandlung rudimentär
- ⚠️ Crawler-Service - Timeout-Handling

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.0.1** | Komplettes Exception-Audit | 1 Tag |
| **v1.1.0** | Standardisiertes Error-Handling | 2 Tage |

---

## ⚙️ **Performance**

### 6. Whisper lädt beim Start

**Status:** 🟡 DOCUMENTED - Lazy-Loading geplant

**Problem:**
- `config/settings.py`: `"load_strategy": "startup"`
- Whisper-Modell (base: ~140MB) lädt beim Backend-Start
- 3-5s Verzögerung auf schwächeren Maschinen

**Auswirkung:**
- Langsamerer Startup
- Höherer RAM-Verbrauch auch wenn STT nicht genutzt wird

**Workaround (aktuell):**
```python
# config/settings.py
"stt": {
    "whisper": {
        "load_strategy": "on_demand",  # statt "startup"
        "model": "base"
    }
}
```

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.3.0** | Lazy Loading (on_demand default) | 1 Tag |
| **v1.3.0** | UI-Toggle für Load-Strategy | 1 Tag |

---

### 7. Keine Shutdown-Sequenz

**Status:** 🟡 DOCUMENTED - Lifecycle-Manager geplant

**Problem:**
- Threads/Queues werden teils unsauber gestoppt
- Keine definierte Shutdown-Reihenfolge
- Potential für:
  - Deadlocks
  - Resource Leaks
  - Ungespeicherte Daten

**Betroffene Komponenten:**
- WebSocket-Server
- Crawler-Service (Thread-Pool)
- TTS-Queue
- LLM-Model-Cache

**Lösung (geplant):**
```python
class LifecycleManager:
    def register(self, component, priority):
        # Components mit Priorität registrieren
        pass
    
    def shutdown(self):
        # Alle Components in reverse order stoppen
        pass
```

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.3.0** | LifecycleManager Implementation | 2-3 Tage |
| **v1.3.0** | Graceful Shutdown Tests | 1 Tag |

---

## ✅ **Testing**

### 8. Test-Coverage gering

**Status:** 🟡 DOCUMENTED - Test-Suite geplant

**Problem:**
- Nur 1 Testmodul: `tests/test_crawler_guard.py`
- Keine Unit-Tests für Core-Module
- Keine Integration-Tests
- Keine CI/CD Pipeline

**Aktuelle Coverage:** ~5%

**Target Coverage (v1.2.0):** 60%+

**Priorität:**
1. **config.Settings** (100%)
2. **utils.Logger** (100%)
3. **core.system.files** (80%)
4. **core.system.processes** (70%)
5. **core.knowledge_manager** (60%)
6. **desktop/backend/bridge** (Go - 60%)

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.2.0** | Unit-Tests (6 Module) | 2 Wochen |
| **v1.2.0** | Integration-Tests | 1 Woche |
| **v1.2.0** | CI/CD Pipeline (GitHub Actions) | 2 Tage |

**Siehe:** `docs/REFACTORING_ROADMAP.md` für Details

---

## 📝 **Dokumentation**

### 9. Type-Hints fehlen teilweise

**Status:** 🟡 DOCUMENTED - Schrittweise Typisierung geplant

**Problem:**
- Viele Funktionen ohne Type-Hints
- Erschwert:
  - Statische Analyse (mypy, pyright)
  - IDE-Autocomplete
  - Refactoring

**Beispiel (aktuell):**
```python
def process_command(self, text):  # Keine Types!
    result = self.parse(text)
    return result
```

**Beispiel (geplant):**
```python
def process_command(self, text: str) -> Dict[str, Any]:
    result: ParseResult = self.parse(text)
    return result.to_dict()
```

**Fixes geplant:**

| Version | Maßnahme | Aufwand |
|---------|-----------|----------|
| **v1.3.0** | Type-Hints Core-Module | Iterativ (1-2h/Modul) |
| **v1.3.0** | mypy --strict Pre-Commit Hook | 1 Tag |

---

## 📊 **Impact-Übersicht**

### **Beeinträchtigt Kernfunktionalität?**

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Token-System | 🟡 MEDIUM | Manueller Token-Sync |
| Shell-Injection | 🟢 LOW | SecurityManager aktiv |
| system_control.py | 🟢 LOW | Funktioniert, nur schwer wartbar |
| TTS-Fragmentierung | 🟢 LOW | XTTS v2 funktioniert |
| Exception-Handling | 🟢 LOW | Meiste Fehler geloggt |
| Whisper-Startup | 🟡 MEDIUM | Config-Flag ändern |
| Shutdown-Sequenz | 🟢 LOW | Meist sauber |
| Test-Coverage | 🟢 LOW | Manuelles Testing |
| Type-Hints | 🟢 LOW | Code funktioniert |

---

## ✅ **System bleibt voll funktionsfähig!**

### **Alle Features arbeiten korrekt:**

- ✅ Chat mit 3 LLM-Modellen (llama3, mistral, deepseek)
- ✅ Voice Control (Whisper STT + XTTS v2 TTS)
- ✅ Knowledge Base (Crawling + Semantic Search)
- ✅ Memory System (Timeline + Search)
- ✅ System Monitoring (CPU/RAM/GPU)
- ✅ Plugin Management (Hot-loading)
- ✅ Security (Passphrase + TOTP 2FA)
- ✅ Auto-Updates (Check + Download)

**Die genannten Limitierungen sind Code-Quality- und Security-Verbesserungen für Production-Readiness, keine funktionalen Einschränkungen.**

---

## 📋 **Release-Zeitplan**

| Version | Focus | Fixes | Release |
|---------|-------|-------|----------|
| **v1.0.0** | ✅ Initial Release | - | 2025-12-05 |
| **v1.0.1** | Security Hardening | #1, #2, #5 (partial) | 2025-12-08 |
| **v1.1.0** | Code Cleanup | #2, #3, #4 | 2025-12-20 |
| **v1.2.0** | Testing | #8 | 2026-01-12 |
| **v1.3.0** | Performance | #6, #7, #9 | 2026-01-26 |

---

## 📞 **Support**

**Fragen zu Known Limitations?**

- **Issues:** [GitHub Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- **Email:** emeyer@fn.de
- **Docs:** `docs/REFACTORING_ROADMAP.md`
- **Security:** `docs/SECURITY_AUDIT.md`

---

**Last Updated:** 2025-12-05 14:30 CET  
**Status:** 🟢 Ready for v1.0.0 Release
