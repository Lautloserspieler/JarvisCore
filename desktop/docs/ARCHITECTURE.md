# Desktop UI - Architektur

## Überblick

Die Desktop-UI ist eine native Anwendung, die über HTTP/WebSocket mit dem bestehenden JarvisCore Python-Backend kommuniziert.

## Komponenten

```
┌───────────────────────────────┐
│   Desktop App (Wails)          │
│                                 │
│  ┌─────────────────────────┐  │
│  │   Vue.js Frontend       │  │
│  └─────────┬────────────────┘  │
│           │ Wails JS Bridge    │
│  ┌─────────┴────────────────┐  │
│  │   Go Backend            │  │
│  │   - App Manager         │  │
│  │   - JarvisCore Bridge   │  │
│  └─────────┬────────────────┘  │
└────────────┼──────────────────┘
              │ HTTP/WebSocket
              │
    ┌─────────┴───────────┐
    │ JarvisCore Python   │
    │ (localhost:5050)    │
    │ - LLM Manager       │
    │ - STT/TTS           │
    │ - Plugins           │
    │ - Knowledge DB      │
    └─────────────────────┘
```

## Kommunikationsflow

1. User-Interaktion in Vue.js
2. Wails Bridge ruft Go-Funktion auf
3. Go sendet HTTP-Request an JarvisCore
4. JarvisCore verarbeitet Request
5. Response zurück durch die Kette
6. Vue.js aktualisiert UI

## Vorteile

- **Wiederverwendung** - Nutzt bestehendes JarvisCore Backend
- **Trennung** - UI unabhängig von Python-Code
- **Performance** - Native Desktop-App
- **Portabilität** - Single Binary für alle Plattformen
