# Go-Services Architektur

## Entscheidung: `go/cmd` als einzige Entry-Struktur

Wir nutzen künftig **`go/cmd` als einzige Entry-Struktur** für Go-basierte Services. Jeder Service hat dort ein eigenes Kommando (z. B. `memoryd`, `securityd`). Dadurch gibt es eine konsistente Startlogik und zentrale Build-/Deployment-Pfade.

## Wiederverwendbarer Code

Alle wiederverwendbaren Komponenten liegen in **`go/internal/`**. Die Entry-Points in `go/cmd` importieren diese Pakete und kapseln nur das Starten, Logging und das Lifecycle-Handling.

## Archivierte Legacy-Module

Die früheren `go-services/`-Module wurden archiviert und liegen nun unter:

- `archive/go-services-legacy/`

Sie dienen nur noch als Referenz und werden nicht mehr aktiv gepflegt.
