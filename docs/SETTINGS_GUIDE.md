# JARVIS Settings Guide

## 🧠 Llama.cpp Inference Settings

### Max Tokens - Intelligent Response Completion

**Default: 2048 Tokens**

#### Wie funktioniert das?

JARVIS nutzt einen **intelligenten Stopp-Mechanismus**, der sicherstellt, dass Antworten **niemals mitten im Satz** abgeschnitten werden:

1. **EOS Token Detection** ✅  
   Das Modell sendet ein "End of Sequence" Token (`</s>`), wenn es seine Antwort beendet hat. JARVIS stoppt dann automatisch, **unabhängig von max_tokens**.

2. **Smart Stopping** ✅  
   llama.cpp erkennt auch andere Stop-Sequenzen wie `<|user|>` und `<|system|>` und hält rechtzeitig.

3. **max_tokens als Sicherheitsnetz** ⚡  
   max_tokens dient nur als **Obergrenze** für sehr lange Antworten. In 99% der Fälle stoppt das Modell **vorher** natürlich durch EOS Token.

#### Empfohlene Werte:

| Modellgröße | max_tokens | Warum? |
|--------------|------------|--------|
| 3B (Llama 3.2, Phi-3) | **2048** | Ausreichend für detaillierte Antworten |
| 7B (Qwen, Mistral) | **2048-4096** | Kann längere, komplexere Antworten geben |
| 8B+ (DeepSeek, Gemma) | **4096** | Maximal detaillierte Erklärungen |

**⚠️ Wichtig:** Ein höherer Wert für max_tokens bedeutet **NICHT** langsamere Antworten! Das Modell stoppt automatisch, wenn die Antwort fertig ist.

#### Was passiert bei zu niedrigen Werten?

**max_tokens = 512:** ❌  
```
User: Erkläre mir neuronale Netzwerke
JARVIS: Ein neuronales Netzwerk ist ein Computermodell...
        [ABGESCHNITTEN MITTEN IM SATZ]
```

**max_tokens = 2048:** ✅  
```
User: Erkläre mir neuronale Netzwerke
JARVIS: Ein neuronales Netzwerk ist ein Computermodell, das...
        [VOLLSTÄNDIGE ERKLÄRUNG]
        
        Zusammenfassend sind neuronale Netzwerke ein 
        mächtiges Werkzeug für KI-Anwendungen.
```

### Temperature (Kreativität)

**Default: 0.7**

- **0.0 - 0.3:** Sehr deterministisch, präzise, technisch  
  👉 Gut für: Code, Fakten, Berechnungen

- **0.4 - 0.8:** Balanced, natürlich, leicht kreativ  
  👉 Gut für: Chat, Erklärungen, Konversation

- **0.9 - 1.5:** Sehr kreativ, variabel, manchmal überraschend  
  👉 Gut für: Storytelling, kreative Ideen

### Top-P (Nucleus Sampling)

**Default: 0.9**

Begrenzt die Token-Auswahl auf die wahrscheinlichsten Optionen:
- **0.9:** Empfohlen - gute Balance
- **0.95:** Etwas diverser
- **1.0:** Keine Begrenzung (kann zu random werden)

### Top-K

**Default: 40**

Begrenzt auf die Top-K wahrscheinlichsten Tokens:
- **40:** Standard-Wert, funktioniert gut
- **20:** Konservativer
- **80:** Diverser

### Repeat Penalty

**Default: 1.1**

Verhindert Wiederholungen:
- **1.0:** Keine Penalty
- **1.1:** Leichte Penalty (empfohlen)
- **1.3+:** Starke Penalty (kann unnötig streng sein)

## 💾 Context Window

**Default: 8192 Tokens**

Die maximale Größe des "Gedächtnisses" für eine Konversation:
- System Prompt: ~200-300 Tokens
- Chat-Historie: Variable
- Neue Nachricht: Variable
- Antwort: bis max_tokens

**Wichtig:** Context Window muss größer sein als max_tokens!

## ⏱️ Performance vs. Qualität

### Schnelle Antworten (3B Modelle):
```json
{
  "max_tokens": 2048,
  "temperature": 0.7,
  "top_p": 0.9
}
```

### Beste Qualität (7B+ Modelle):
```json
{
  "max_tokens": 4096,
  "temperature": 0.7,
  "top_p": 0.95
}
```

### Präzise technische Antworten:
```json
{
  "max_tokens": 2048,
  "temperature": 0.3,
  "top_p": 0.9
}
```

## 🔧 Tipps & Tricks

1. **Antworten werden abgeschnitten?**  
   → Erhöhe max_tokens auf 2048 oder höher

2. **Antworten zu repetitiv?**  
   → Erhöhe repeat_penalty auf 1.2

3. **Antworten zu "random"?**  
   → Senke temperature auf 0.5-0.6

4. **Antworten zu "langweilig"?**  
   → Erhöhe temperature auf 0.8-0.9

5. **Model läuft zu langsam?**  
   → Nutze kleineres Modell (3B statt 7B) oder aktiviere GPU

## 🎯 Recommended Presets

### Default (Balanced)
```json
{
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "repeat_penalty": 1.1,
  "max_tokens": 2048
}
```

### Technical Assistant
```json
{
  "temperature": 0.4,
  "top_p": 0.9,
  "top_k": 30,
  "repeat_penalty": 1.1,
  "max_tokens": 2048
}
```

### Creative Chatbot
```json
{
  "temperature": 0.9,
  "top_p": 0.95,
  "top_k": 50,
  "repeat_penalty": 1.15,
  "max_tokens": 3072
}
```

## ❓ FAQ

**Q: Warum stoppt JARVIS manchmal vor max_tokens?**  
A: Das ist **gewollt**! Das Modell sendet ein EOS Token wenn die Antwort fertig ist. max_tokens ist nur eine Obergrenze.

**Q: Kann ich max_tokens auf 10000 setzen?**  
A: Ja, aber achte darauf dass es kleiner als context_window ist. Für die meisten Use-Cases reichen 2048-4096.

**Q: Macht ein höherer max_tokens die Generierung langsamer?**  
A: **Nein!** Das Modell stoppt automatisch. Ein höherer Wert ist nur eine Sicherheit.

**Q: Was ist besser: Hohe temperature oder hoher top_p?**  
A: **Beides zusammen!** Temperature kontrolliert Randomness, top_p begrenzt die Auswahl. Nutze beide.

---

**Made with ❤️ for JARVIS Core v1.1.0**