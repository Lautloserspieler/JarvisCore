#!/bin/bash
# Automatisches Komplettes Refactoring - Shell Script

set -e  # Exit on error

echo "========================================"
echo "🚀 JarvisCore - Auto Refactoring"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    exit 1
fi

echo "🔍 Prüfe Git Status..."
git status --short

echo ""
echo "⚠️  WARNUNG: Dieses Script führt folgende Änderungen durch:"
echo "  1. Löscht webapp/ Verzeichnis"
echo "  2. Reorganisiert core/ Module"
echo "  3. Aktualisiert alle Imports"
echo "  4. Erstellt Git Commit"
echo ""

read -p "🚀 Fortfahren? (j/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "🚀 Starte automatisches Refactoring..."
echo ""

# Run Python script
python3 scripts/auto_refactor.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Refactoring erfolgreich abgeschlossen!"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. git push origin main"
    echo "  2. pytest  # Tests ausführen"
    echo "  3. cd desktop && wails dev  # Desktop-App testen"
    echo ""
else
    echo ""
    echo "❌ Refactoring fehlgeschlagen (Exit Code: $EXIT_CODE)"
    echo "Siehe Logs für Details."
    echo ""
    exit $EXIT_CODE
fi
