@echo off
REM Build script for JarvisCore Desktop (Windows)

echo [BUILD] JarvisCore Desktop
echo.

REM Get version from git tag or use default
for /f "delims=" %%i in ('git describe --tags --exact-match 2^>nul') do set VERSION=%%i

if "%VERSION%"=="" (
    set VERSION=v1.0.0-dev
    echo [WARN] No git tag found, using default: %VERSION%
) else (
    echo [INFO] Building with git tag: %VERSION%
)

echo.
echo [BUILD] Compiling binary...
echo.

wails build -ldflags "-X 'github.com/Lautloserspieler/JarvisCore/desktop/backend/internal/app.Version=%VERSION%'"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Build completed!
    echo [INFO] Binary: build\bin\
    echo [INFO] Version: %VERSION%
) else (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)
