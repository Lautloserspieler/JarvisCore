\# Sicherheit



\## Kryptografie



\- \[translate:AES-256] zur symmetrischen Verschlüsselung.

\- \[translate:RSA-4096] für Schlüsseltausch und Signatur.



\## Rollen \& Rechte



\- Rollenbasiertes Zugriffssystem:

&nbsp; - z. B. Admin, User, Gast (je nach Konfiguration).

\- Einschränkungen:

&nbsp; - Dateisystem-Zugriff

&nbsp; - Netzwerk-Zugriff

&nbsp; - Ausführung externer Programme



\## Safe-Mode



\- Safe-Mode kann in der Konfiguration aktiviert werden.

\- Beschränkt die erlaubten Aktionen auf einen sicheren Subset.



\## Logging



\- Sicherheitsrelevante Ereignisse werden nachverfolgt.

\- Relevante Dateien:

&nbsp; - `logs/security.log`

&nbsp; - ggf. weitere Audit-Logs.



\## Notfallprotokoll



\- Geplante Mechanismen für:

&nbsp; - Sperrung von Accounts/Tokens.

&nbsp; - kontrollierten Shutdown.

&nbsp; - Alerts (z. B. an Admin).

