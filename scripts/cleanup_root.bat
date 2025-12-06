@echo off
REM Windows Batch Script for Root Cleanup

echo ============================================================
echo ROOT DIRECTORY CLEANUP
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

REM Ask for confirmation
echo This will clean up the root directory:
echo   - Move docs to docs/
echo   - Delete redundant scripts
echo   - Remove webapp/
echo.
set /p CONFIRM=Continue? (y/n): 

if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Running cleanup script...
echo.

python scripts\cleanup_root.py --execute

if errorlevel 1 (
    echo.
    echo ERROR: Cleanup failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo CLEANUP COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo   git add .
echo   git commit -m "chore: cleanup root directory"
echo   git push origin cleanup/root-directory
echo.
pause
