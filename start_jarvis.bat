@echo off
REM J.A.R.V.I.S. Core - Windows Launcher
REM Startet automatisch Backend + Desktop UI

title J.A.R.V.I.S. Core Launcher

echo.
echo ============================================================
echo              J.A.R.V.I.S. Core Launcher v1.0.0
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nicht gefunden!
    echo [INFO] Bitte Python 3.10+ installieren: https://www.python.org
    pause
    exit /b 1
)

REM Check if start_jarvis.py exists
if not exist "start_jarvis.py" (
    echo [ERROR] start_jarvis.py nicht gefunden!
    echo [INFO] Bitte im JarvisCore-Verzeichnis ausfuehren
    pause
    exit /b 1
)

REM Start unified launcher
echo [INFO] Starte J.A.R.V.I.S. Core...
echo.
python start_jarvis.py %*

REM Exit code handling
if errorlevel 1 (
    echo.
    echo [ERROR] Fehler beim Starten!
    pause
    exit /b 1
)

pause
