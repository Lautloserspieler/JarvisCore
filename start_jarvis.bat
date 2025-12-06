@echo off
REM J.A.R.V.I.S. Core - Windows Starter
REM Automatischer Start mit ImGui Desktop-UI

echo ========================================
echo  J.A.R.V.I.S. Core - Starter
echo ========================================
echo.

REM Prüfe ob venv existiert
if not exist "venv\Scripts\activate.bat" (
    echo [FEHLER] Virtuelle Umgebung nicht gefunden!
    echo Bitte zuerst Setup ausführen: python setup.py
    pause
    exit /b 1
)

REM Aktiviere venv
echo [INFO] Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

REM Setze Environment Variable
set JARVIS_DESKTOP=1

REM Starte JARVIS
echo [INFO] Starte J.A.R.V.I.S. mit ImGui Desktop-UI...
echo.
python main.py

REM Deaktiviere venv
deactivate

echo.
echo [INFO] J.A.R.V.I.S. wurde beendet.
pause
