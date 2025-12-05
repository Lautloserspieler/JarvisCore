@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ---------------------------------------------------------------------------
REM Stelle sicher, dass Microsoft C++ Build Tools mit VC-Toolset installiert sind.
REM 1) Wenn cl.exe fehlt: winget-Installation inkl. VCTools-Workload.
REM 2) Aktiviere danach die MSVC-Umgebung ueber VsDevCmd.bat, falls vorhanden.
REM ---------------------------------------------------------------------------
powershell -NoProfile -Command ^
  "$cl = Get-Command cl.exe -ErrorAction SilentlyContinue;" ^
  "if (-not $cl) {" ^
  "  Write-Host '[setup] Microsoft C++ Build Tools nicht gefunden. Starte winget-Installation...' -ForegroundColor Yellow;" ^
  "  $pkg = 'Microsoft.VisualStudio.2022.BuildTools';" ^
  "  $args = '--override', '--passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --includeOptional';" ^
  "  if (Get-Command winget -ErrorAction SilentlyContinue) {" ^
  "    winget install --id $pkg --silent --accept-package-agreements --accept-source-agreements @args;" ^
  "  } else {" ^
  "    Write-Host '[setup] winget nicht verfuegbar. Lade Offline-Installer...' -ForegroundColor Red;" ^
  "    $url = 'https://aka.ms/vs/17/release/vs_BuildTools.exe';" ^
  "    $tmp = Join-Path $env:TEMP 'vs_BuildTools.exe';" ^
  "    Invoke-WebRequest $url -OutFile $tmp;" ^
  "    Start-Process -FilePath $tmp -ArgumentList '--passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --includeOptional' -Wait;" ^
  "  }" ^
  "}"

REM Finde VsDevCmd und aktiviere MSVC-Umgebung fuer den aktuellen Prozess
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2^>NUL`) do set "VSINSTALL=%%i"
if defined VSINSTALL (
    set "VSDEV=%VSINSTALL%\Common7\Tools\VsDevCmd.bat"
    if exist "%VSDEV%" (
        call "%VSDEV%" -startdir=none -arch=x64 -host_arch=x64
    )
)

echo [run] Starte Bootstrap (Installation + Launch)...
py -3.11 bootstrap.py --run %*

if errorlevel 1 (
    echo.
    echo [run] Fehler aufgetreten. Log-Ausgabe siehe oben.
    pause
) else (
    echo.
    echo [run] Vorgang abgeschlossen.
)
