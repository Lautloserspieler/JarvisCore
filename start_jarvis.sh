#!/bin/bash
# J.A.R.V.I.S. Core - Linux/macOS Launcher
# Startet automatisch Backend + Desktop UI

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "============================================================"
echo "            J.A.R.V.I.S. Core Launcher v1.0.0"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 nicht gefunden!"
    echo -e "${YELLOW}[INFO]${NC} Bitte Python 3.10+ installieren"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}[ERROR]${NC} Python $PYTHON_VERSION gefunden, aber $REQUIRED_VERSION+ erforderlich!"
    exit 1
fi

# Check if start_jarvis.py exists
if [ ! -f "start_jarvis.py" ]; then
    echo -e "${RED}[ERROR]${NC} start_jarvis.py nicht gefunden!"
    echo -e "${YELLOW}[INFO]${NC} Bitte im JarvisCore-Verzeichnis ausführen"
    exit 1
fi

# Make script executable if not already
chmod +x start_jarvis.py 2>/dev/null || true

# Start unified launcher
echo -e "${GREEN}[INFO]${NC} Starte J.A.R.V.I.S. Core..."
echo ""

python3 start_jarvis.py "$@"

# Exit code handling
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERROR]${NC} Fehler beim Starten!"
    exit 1
fi
