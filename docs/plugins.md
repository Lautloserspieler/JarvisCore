\# Plugins



\## Konzept



JarvisCore ist modular aufgebaut und kann über Plugins erweitert werden.



Typische Anwendungsfälle:



\- System-Automatisierung (Dateien, Prozesse, Tools).

\- Wissens-Erweiterung (Crawler, APIs).

\- Spezielle Assistenzfunktionen (GameDev-Tools, DevOps, etc.).



\## Struktur



Beispiel:



plugins/

├─ example\_plugin/

│ ├─ init.py

│ └─ plugin.py



text



Ein Plugin kann u. a.:



\- Metadaten bereitstellen (Name, Beschreibung, Version).

\- Hooks registrieren (z. B. auf neue Nachrichten).

\- eigene Konfiguration und ggf. Endpunkte anbieten.



\## Lebenszyklus



\- Beim Start scannt JarvisCore den `plugins/`-Ordner.

\- Gefundene Plugins werden geladen und initialisiert.

\- Aktivierung/Deaktivierung per Web-UI.



\## Sicherheit



\- Jedes Plugin sollte klar definierte Rechte haben.

\- Kritische Aktionen sollten nur in Kombination mit Safe-Mode/Rollen erlaubt sein.

