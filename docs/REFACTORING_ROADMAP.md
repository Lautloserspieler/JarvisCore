# Refactoring Roadmap

**Status:** 🟡 Planned  
**Target:** v1.1.0 - v1.3.0  

---

## 🎯 Ziele

1. **Code Quality:** Wartbarkeit verbessern
2. **Security:** Shell-Injection-Risiken eliminieren
3. **Performance:** Lazy Loading implementieren
4. **Testing:** 60%+ Test-Coverage

---

## 📍 v1.1.0 - Code Struktur (1-2 Wochen)

### **1. system_control.py aufteilen**

**Problem:**  
- ~1600 Zeilen in einer Datei
- Mischt verschiedene Concerns
- Schwer zu testen

**Lösung:**

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

1. Tests schreiben für aktuelle Funktionalität
2. Modul-by-Modul extrahieren
3. Integration-Tests laufen lassen
4. Legacy-Code entfernen

**Aufwand:** 3-4 Tage

---

### **2. Shell-Injection eliminieren**

**Problem:**  
- `shell=True` an mehreren Stellen
- Potenzielle Security-Risks

**Lösung:**

```python
# core/system/shell.py

from typing import List, Dict, Any
import subprocess
import shlex

class SafeShell:
    """Secure Shell Command Executor"""
    
    # Whitelist erlaubter Commands
    ALLOWED_COMMANDS = {
        'netsh', 'attrib', 'taskkill', 'pkill',
        'shutdown', 'reboot', 'cmd', 'powershell'
    }
    
    def run(self, command: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Execute command with security checks"""
        if not command:
            raise ValueError("Empty command")
        
        # Validate command against whitelist
        if command[0] not in self.ALLOWED_COMMANDS:
            raise PermissionError(f"Command not allowed: {command[0]}")
        
        # ALWAYS shell=False
        return subprocess.run(
            command,
            shell=False,  # NEVER True!
            **kwargs
        )
    
    def run_safe(self, command_str: str, **kwargs) -> subprocess.CompletedProcess:
        """Parse string to list and run safely"""
        command = shlex.split(command_str)  # Safe parsing
        return self.run(command, **kwargs)
```

**Migration:**

```python
# OLD:
subprocess.run(f"netsh interface set {name}", shell=True)

# NEW:
safe_shell = SafeShell()
safe_shell.run(["netsh", "interface", "set", name])
```

**Aufwand:** 2-3 Tage

---

### **3. TTS-Konsolidierung**

**Problem:**  
- 5 verschiedene TTS-Implementierungen
- Verwirrend für Entwickler
- Doppelte Logik

**Aktuelle Dateien:**
```
core/
├── text_to_speech.py      # Legacy
├── reliable_tts.py        # Queue-based
├── xtts_tts.py            # XTTS v1
├── xtts_tts_fixed.py      # XTTS v1 Fix
├── xttsv2_tts.py          # XTTS v2 ✅
└── xttsv2_clone.py        # Voice Cloning ✅
```

**Neue Struktur:**

```
core/tts/
├── __init__.py           # Public API
├── base.py              # ITTSProvider Interface
├── xtts_v2.py           # XTTS v2 Implementation ✅
├── voice_cloning.py     # Voice Cloning ✅
└── legacy/              # Alte Implementierungen
    ├── text_to_speech.py
    ├── reliable_tts.py
    ├── xtts_tts.py
    └── xtts_tts_fixed.py
```

**Interface:**

```python
# core/tts/base.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class ITTSProvider(ABC):
    """TTS Provider Interface"""
    
    @abstractmethod
    def speak(self, text: str, **kwargs) -> bool:
        """Speak text synchronously"""
        pass
    
    @abstractmethod
    def speak_async(self, text: str, **kwargs) -> None:
        """Speak text asynchronously"""
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Change voice"""
        pass
    
    @abstractmethod
    def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop current playback"""
        pass
```

**Usage:**

```python
# main.py

from core.tts import XTTSv2Provider

tts = XTTSv2Provider()
tts.set_voice("de_female_1")
tts.speak("Hallo Welt")
```

**Aufwand:** 2-3 Tage

---

## 📍 v1.2.0 - Testing (2-3 Wochen)

### **Test-Coverage: 60%+**

**Target Modules:**

1. **config.Settings** (100%)
   - Loading/Saving
   - Validation
   - Defaults

2. **utils.Logger** (100%)
   - Rotating Logs
   - Level-Filtering
   - Stats

3. **core.system.files** (80%)
   - Read/Write Operations
   - Permission Checks
   - Path Validation

4. **core.system.processes** (70%)
   - Start/Stop Programs
   - Process Listing
   - Kill Operations

5. **core.knowledge_manager** (60%)
   - Query Operations
   - Indexing
   - Storage

6. **desktop/backend/bridge** (Go - 60%)
   - HTTP Requests
   - WebSocket Connection
   - Error Handling

**Test-Struktur:**

```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_system_files.py
│   ├── test_system_processes.py
│   └── test_knowledge_manager.py
├── integration/
│   ├── test_api_bridge.py       # Go ↔ Python
│   ├── test_websocket.py        # WebSocket Flow
│   └── test_crawler.py          # Crawler Service
├── fixtures/
│   ├── test_data.json
│   └── mock_responses.json
└── conftest.py              # Pytest Config
```

**CI/CD:**

```yaml
# .github/workflows/tests.yml

name: Tests

on: [push, pull_request]

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=core --cov=utils --cov-report=xml
      - uses: codecov/codecov-action@v3
```

**Aufwand:** 2-3 Wochen

---

## 📍 v1.3.0 - Performance & Polish (2 Wochen)

### **1. Lazy Loading**

**Problem:**  
- Whisper lädt beim Start (3-5s Verzögerung)
- LLM Models werden alle gecacht

**Lösung:**

```python
# config/settings.py

"stt": {
    "whisper": {
        "enabled": True,
        "load_strategy": "on_demand",  # statt "startup"
        "model": "base"
    }
}

# core/speech_manager.py

class SpeechManager:
    def __init__(self):
        self.whisper = None  # Nicht sofort laden
    
    def _ensure_whisper(self):
        """Lazy load Whisper"""
        if self.whisper is None:
            self.whisper = whisper.load_model("base")
    
    def transcribe(self, audio):
        self._ensure_whisper()  # Laden bei erstem Use
        return self.whisper.transcribe(audio)
```

**Aufwand:** 1-2 Tage

---

### **2. Lifecycle-Manager**

**Problem:**  
- Threads/Queues werden unsauber gestoppt
- Potential für Deadlocks

**Lösung:**

```python
# core/lifecycle.py

class LifecycleManager:
    """Zentrale Steuerung für Startup/Shutdown"""
    
    def __init__(self):
        self.components = []  # Registered components
    
    def register(self, component, priority=0):
        """Register component with shutdown priority"""
        self.components.append((priority, component))
        self.components.sort(key=lambda x: x[0])  # Sort by priority
    
    def startup(self):
        """Start all components in order"""
        for _, component in self.components:
            if hasattr(component, 'startup'):
                component.startup()
    
    def shutdown(self):
        """Stop all components in reverse order"""
        for _, component in reversed(self.components):
            if hasattr(component, 'shutdown'):
                try:
                    component.shutdown()
                except Exception as e:
                    logger.error(f"Shutdown failed for {component}: {e}")
```

**Usage:**

```python
# main.py

lifecycle = LifecycleManager()
lifecycle.register(speech_manager, priority=1)
lifecycle.register(llm_manager, priority=2)
lifecycle.register(knowledge_manager, priority=3)

lifecycle.startup()

try:
    # Run application
    pass
finally:
    lifecycle.shutdown()  # Clean exit
```

**Aufwand:** 2-3 Tage

---

### **3. Type-Hints (schrittweise)**

**Tools:**
- `mypy` für statische Typ-Prüfung
- `pyright` für IDE-Support

**Prä-Commit Hook:**

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--strict]
        files: ^(core|utils)/
```

**Aufwand:** Iterativ (1-2 Std pro Modul)

---

## 📋 Zeitplan

| Version | Inhalt | Aufwand | Start | Release |
|---------|--------|---------|-------|----------|
| **v1.0.1** | Token + Shell Audit | 2 Tage | 2025-12-06 | 2025-12-08 |
| **v1.1.0** | Code Refactoring | 2 Wochen | 2025-12-09 | 2025-12-20 |
| **v1.2.0** | Testing | 3 Wochen | 2025-12-23 | 2026-01-12 |
| **v1.3.0** | Performance | 2 Wochen | 2026-01-13 | 2026-01-26 |

---

## ✅ Erfolgsmetriken

### **v1.1.0:**
- [ ] `system_control.py` aufgeteilt in 7 Module
- [ ] Alle `shell=True` durch `shell=False` ersetzt
- [ ] TTS auf 2 Implementierungen reduziert (XTTS v2 + Legacy)
- [ ] Code-Review durchgeführt

### **v1.2.0:**
- [ ] Test-Coverage ≥ 60%
- [ ] CI/CD Pipeline läuft
- [ ] Keine failing Tests
- [ ] Code-Coverage Badge im README

### **v1.3.0:**
- [ ] Startup-Zeit ≤ 3s (Backend + Desktop)
- [ ] Alle Threads sauber gestoppt
- [ ] Type-Hints in allen Core-Modulen
- [ ] mypy --strict passiert

---

## 👨‍💻 Contributor Guide

**Pull Requests für Refactorings:**

1. **Issue erstellen** mit Beschreibung
2. **Branch** erstellen: `refactor/system-control-split`
3. **Tests** schreiben BEVOR Code geändert wird
4. **Schrittweise** migrieren (nicht alles auf einmal)
5. **Review** Request an @Lautloserspieler

---

**Status:** 🟡 Ready for v1.1.0 Planning
