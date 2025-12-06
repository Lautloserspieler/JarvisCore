@echo off
REM Automatisches Komplettes Refactoring - Batch Script

echo ========================================
echo 🚀 JarvisCore - Auto Refactoring
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nicht gefunden!
    exit /b 1
)

echo 🔍 Prüfe Git Status...
git status --short

echo.
echo ⚠️  WARNUNG: Dieses Script führt folgende Änderungen durch:
echo   1. Löscht webapp\ Verzeichnis
echo   2. Reorganisiert core\ Module
echo   3. Aktualisiert alle Imports
echo   4. Erstellt Git Commit
echo.

set /p CONFIRM="🚀 Fortfahren? (j/n): "
if /i not "%CONFIRM%"=="j" (
    echo Abgebrochen.
    exit /b 0
)

echo.
echo 🚀 Starte automatisches Refactoring...
echo.

REM Run Python script
python scripts\auto_refactor.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Refactoring erfolgreich abgeschlossen!
    echo.
    echo Nächste Schritte:
    echo   1. git push origin main
    echo   2. pytest  REM Tests ausführen
    echo   3. cd desktop ^&^& wails dev  REM Desktop-App testen
    echo.
) else (
    echo.
    echo ❌ Refactoring fehlgeschlagen (Exit Code: %errorlevel%)
    echo Siehe Logs für Details.
    echo.
    exit /b %errorlevel%
)
