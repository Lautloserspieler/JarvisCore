# Sicherheitsrichtlinie

## Unterstützte Versionen

Wir veröffentlichen Patches für Sicherheitslücken in den folgenden Versionen:

| Version | Unterstützt          |
| ------- | --------------------- |
| 1.1.x   | :white_check_mark:    |
| 1.0.x   | :white_check_mark:    |
| < 1.0   | :x:                   |

## Meldung einer Sicherheitslücke

Wir nehmen die Sicherheit von JarvisCore ernst. Wenn Sie glauben, eine Sicherheitslücke gefunden zu haben, melden Sie sie uns bitte wie unten beschrieben.

### Wie melden

**Bitte melden Sie Sicherheitslücken NICHT über öffentliche GitHub Issues.**

Melden Sie sie stattdessen über eine der folgenden Methoden:

1. **E-Mail**: Senden Sie Details an [SICHERHEITS-EMAIL EINFÜGEN]
2. **GitHub Security Advisory**: Nutzen Sie die [Security Advisory](https://github.com/Lautloserspieler/JarvisCore/security/advisories) Funktion

### Was einschließen

Bitte fügen Sie folgende Informationen in Ihre Meldung ein:

- Art der Schwachstelle (z.B. Buffer Overflow, SQL Injection, Cross-Site Scripting, etc.)
- Vollständige Pfade der Quelldateien im Zusammenhang mit der Schwachstelle
- Ort des betroffenen Quellcodes (Tag/Branch/Commit oder direkte URL)
- Spezielle Konfiguration, die zur Reproduktion erforderlich ist
- Schritt-für-Schritt-Anleitung zur Reproduktion des Problems
- Proof-of-Concept oder Exploit-Code (falls möglich)
- Auswirkung der Schwachstelle, einschließlich wie ein Angreifer sie ausnutzen könnte

### Antwort-Zeitplan

Wir bestätigen den Erhalt Ihrer Meldung innerhalb von **48 Stunden** und senden Ihnen regelmäßige Updates über unseren Fortschritt.

- **Erste Antwort**: Innerhalb von 48 Stunden
- **Status-Update**: Innerhalb von 7 Tagen
- **Lösungs-Ziel**: Innerhalb von 90 Tagen für kritische Schwachstellen

### Veröffentlichungsrichtlinie

Wir folgen einem koordinierten Veröffentlichungsprozess:

1. Sie melden die Schwachstelle privat
2. Wir bestätigen die Schwachstelle und arbeiten an einer Lösung
3. Wir veröffentlichen ein Sicherheitsupdate
4. Nach breiter Verteilung des Fixes veröffentlichen wir die Schwachstelle (typischerweise 30 Tage nach dem Fix)

### Bug Bounty

Derzeit bieten wir kein bezahltes Bug-Bounty-Programm an. Jedoch schätzen wir die Bemühungen der Sicherheits-Community sehr und werden:

- Ihren Beitrag öffentlich anerkennen (wenn Sie möchten)
- Frühzeitigen Zugang zu neuen Features bieten

## Sicherheits-Best-Practices für Benutzer

Beim Deployment von JarvisCore folgen Sie bitte diesen Sicherheits-Best-Practices:

### 1. Software aktuell halten

- Verwenden Sie immer die neueste stabile Version
- Aktivieren Sie automatische Sicherheitsupdates wo möglich
- Abonnieren Sie unsere [Sicherheitsankündigungen](https://github.com/Lautloserspieler/JarvisCore/security/advisories)

### 2. Netzwerksicherheit

- JarvisCore hinter einer Firewall betreiben
- HTTPS für alle Web-Interfaces verwenden
- Netzwerkzugriff nur auf vertrauenswürdige Netzwerke beschränken
- VPN für Remote-Zugriff in Betracht ziehen

### 3. Zugriffskontrolle

- Starke, einzigartige Passwörter verwenden
- Authentifizierung für alle Services aktivieren
- Prinzip der minimalen Rechte implementieren
- Zugangsdaten regelmäßig prüfen und rotieren

### 4. Datenschutz

- Sensible Daten verschlüsselt speichern
- Sichere Kommunikationskanäle verwenden (TLS/SSL)
- Regelmäßige Backups kritischer Daten
- Sensible Daten sicher löschen, wenn nicht mehr benötigt

### 5. Docker-Sicherheit

- Nur offizielle Docker-Images verwenden
- Docker und Container-Images aktuell halten
- Container als Nicht-Root-Benutzer ausführen wo möglich
- Docker Secrets für sensible Konfiguration verwenden
- Images regelmäßig auf Schwachstellen scannen

### 6. Modell-Sicherheit

- Modelle nur aus vertrauenswürdigen Quellen herunterladen
- Modell-Prüfsummen/Signaturen verifizieren
- Vorsicht bei benutzerdefinierten Prompts
- Input-Validierung und -Bereinigung implementieren

### 7. Überwachung und Logging

- Umfassendes Logging aktivieren
- Auf verdächtige Aktivitäten überwachen
- Benachrichtigungen für Sicherheitsereignisse einrichten
- Logs regelmäßig prüfen

## Bekannte Sicherheitsüberlegungen

### Lokale KI-Modelle

- JarvisCore führt KI-Modelle lokal aus, was bedeutet, dass sie Zugriff auf Systemressourcen haben
- Stellen Sie sicher, dass Modelle aus vertrauenswürdigen Quellen stammen
- Seien Sie sich potenzieller Prompt-Injection-Angriffe bewusst

### Sprachverarbeitung

- Audiodaten werden lokal aus Datenschutzgründen verarbeitet
- Stellen Sie sicher, dass der Mikrofonzugriff ordnungsgemäß gesichert ist
- Achten Sie auf physische Sicherheit bei Verwendung von Sprachfunktionen

### Plugin-System

- Drittanbieter-Plugins laufen mit Systemprivilegien
- Installieren Sie nur Plugins aus vertrauenswürdigen Quellen
- Überprüfen Sie Plugin-Code vor der Installation
- Halten Sie Plugins aktuell

### Datenschutz

- Alle Datenverarbeitung erfolgt standardmäßig lokal
- Keine Telemetrie oder Analytik werden ohne ausdrückliche Zustimmung gesendet
- Überprüfen Sie Datenschutzeinstellungen regelmäßig

## Sicherheitsupdates

Sicherheitsupdates werden wie folgt veröffentlicht:

- **Kritisch**: Sofortiger Patch-Release
- **Hoch**: Innerhalb von 7 Tagen
- **Mittel**: Innerhalb von 30 Tagen
- **Niedrig**: Nächster regulärer Release

## Compliance

JarvisCore ist mit Blick auf Datenschutz und Sicherheit konzipiert:

- **DSGVO**: Vollständig konform bei Konfiguration für rein lokalen Betrieb
- **Datenminimierung**: Sammelt nur für Funktionalität notwendige Daten
- **Recht auf Löschung**: Alle Daten können vom Benutzer gelöscht werden
- **Transparenz**: Open-Source-Codebasis für vollständige Prüfbarkeit

## Sicherheitsaudit

Wir begrüßen Sicherheitsaudits von JarvisCore. Wenn Sie an einem Sicherheitsaudit interessiert sind:

1. Kontaktieren Sie uns unter [SICHERHEITS-EMAIL EINFÜGEN]
2. Wir stellen Anleitung und Zugang nach Bedarf bereit
3. Ergebnisse können nach Belieben öffentlich oder privat geteilt werden

## Hall of Fame

Wir danken den folgenden Sicherheitsforschern für die verantwortungsvolle Offenlegung von Schwachstellen:

<!-- Liste wird gefüllt, sobald Schwachstellen gemeldet und behoben wurden -->

*Bisher wurden keine Schwachstellen gemeldet.*

## Zusätzliche Ressourcen

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

## Fragen?

Wenn Sie Fragen zu dieser Sicherheitsrichtlinie haben, kontaktieren Sie uns bitte unter [SICHERHEITS-EMAIL EINFÜGEN].

---

**Zuletzt aktualisiert**: 16. Dezember 2025  
**Nächste Überprüfung**: 16. März 2026
