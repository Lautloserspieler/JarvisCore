# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### Hinweis
- ⚠️ **Voice-Features (TTS/Whisper) sind derzeit nicht Teil eines Releases.** Die folgenden Einträge beschreiben geplante/experimentelle Arbeit und sind noch nicht ausgeliefert.

### Added
- 🇩🇪 **Multilingual Voice Cloning mit Language-Aware Caching**
  - Separate Voice Latents pro Sprache (Deutsch, Englisch)
  - Auto-Language Detection aus Text
  - Intelligentes Caching: ~2s Einmalig, dann <10ms
  - Language-specific Voice Sample Selection
  - Dynamisches Language Switching ohne Modell-Reload
  - Neue Methoden: `_detect_language()`, `_get_latents_cache_path()`, `_prepare_xtts_conditioning(language)`
  - Erweiterte `speak()` API mit optionalem `language` Parameter
  - Vollständige Rückwärts-Kompatibilität mit Single-Language Setup

### Changed
- **TTS Queue-Format:** `(text, style)` → `(text, style, language)`
  - Alt: `tts.speak("Hello", style='neutral')`
  - Neu: `tts.speak("Hello", style='neutral', language='en')`  
  - Alt funktioniert immer noch (language wird auto-detected)

- **Voice Latents Caching:** 
  - Alt: `data/tts/xtts_voice_latents.pt` (allgemein)
  - Neu: `data/tts/voice_latents_de.pt` + `data/tts/voice_latents_en.pt` (pro Sprache)
  - Legacy-Cache wird automatisch ignoriert (kein Konflikt)

### Performance
- First German call: ~2-3 Sekunden (Voice Clone Computation)
- Subsequent German calls: <1 Sekunde (aus Cache)
- Language switching: <10ms (nur Latents-Wechsel)
- **Gesamt:** ~50% schneller bei mehrsprachiger Verwendung vs. wiederholte Voice Cloning

### Documentation
- Neue Datei: `docs/MULTILINGUAL_VOICE_CLONING.md`
  - Detaillierte Konfigurationsbeispiele
  - Voice Sample Preparation Guide
  - Performance Characteristics
  - Troubleshooting & Best Practices
  - Migration Guide von Single-Language Setup

### Testing
- Neue Test-Suite: `tests/test_multilingual_tts.py`
  - Language Auto-Detection Tests (9 Tests)
  - Voice Latents Caching Tests (4 Tests)
  - Queue & API Tests (4 Tests)
  - Configuration Migration Tests (3 Tests)
  - Performance Benchmarks (2 Tests)
  - Error Handling Tests (3 Tests)
  - Integration Tests (1 Test)
  - Insgesamt: 26 Tests

### Configuration Example

```yaml
speech:
  tts_backend: 'xtts'
  tts_rate: 180
  tts_volume: 0.8
  tts_use_gpu: true
  
  # Neue: Sprachspezifische Voice Samples
  voice_sample_de: 'models/tts/voices/Jarvis_DE.wav'
  voice_sample_en: 'models/tts/voices/Jarvis_EN.wav'
  
  # Fallback (alt)
  voice_sample: 'models/tts/voices/Jarvis.wav'
```

### API Usage Example

```python
# Auto-Language Detection
tts.speak("Hallo!")              # → German
tts.speak("Hello!")              # → English

# Explicit Language
tts.speak("Test", language='de')
tts.speak("Test", language='en')

# With Style
tts.speak("Super!", language='de', style='freundlich')

# Old API (still works!)
tts.speak("Test", style='neutral')  # Language auto-detected
```

---

## [Versionen vor 2025-12-20]

(Frühere Releases...)
