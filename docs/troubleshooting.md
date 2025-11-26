\# Fehlerbehebung



\## Häufige Probleme



\### CUDA nicht verfügbar – CPU-Fallback



\- Prüfe, ob:

&nbsp; - NVIDIA-Treiber aktuell sind.

&nbsp; - CUDA ≥ 12.0 installiert ist.

\- Falls nicht: CUDA installieren, neu booten und JarvisCore neu starten.



\### PyAudio Fehler



\- Unter Windows: „Microsoft C++ Build Tools“ installieren.

\- Danach ggf. virtuelle Umgebung neu erstellen und Abhängigkeiten neu installieren.



\### Ignoring invalid distribution



\- `venv/` löschen.

\- Virtuelle Umgebung neu anlegen.

\- `pip install -r requirements.txt` erneut ausführen.



\### Modelle laden sehr lange



\- Beim ersten Start werden teils mehrere GB heruntergeladen.

\- Folge-Starts nutzen den Cache in `models/`.



\### Web-UI leer oder 401 Unauthorized



\- Token in `data/settings.json` prüfen.

\- Logs (`logs/`, insbesondere `jarvis.log`) prüfen.



\### AMD-GPUs werden nicht genutzt



\- Aktuell Fokus auf NVIDIA/CUDA.

\- JarvisCore funktioniert auch im CPU-Modus (langsamer).

