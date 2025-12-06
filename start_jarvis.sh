#!/bin/bash
# J.A.R.V.I.S. Core - Linux/macOS Starter
# Automatischer Start mit ImGui Desktop-UI

set -e

echo "========================================"
echo "  J.A.R.V.I.S. Core - Starter"
echo "========================================"
echo ""

# Prüfe ob venv existiert
if [ ! -f "venv/bin/activate" ]; then
    echo "[FEHLER] Virtuelle Umgebung nicht gefunden!"
    echo "Bitte zuerst Setup ausführen: python3 setup.py"
    exit 1
fi

# Aktiviere venv
echo "[INFO] Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Setze Environment Variable
export JARVIS_DESKTOP=1

# Starte JARVIS
echo "[INFO] Starte J.A.R.V.I.S. mit ImGui Desktop-UI..."
echo ""
python main.py

# Deaktiviere venv
deactivate

echo ""
echo "[INFO] J.A.R.V.I.S. wurde beendet."
