#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Hinweis: Microsoft C++ Build Tools (cl.exe) werden fuer das Bauen nativer Abhaengigkeiten benoetigt."
if command -v cmd.exe >/dev/null 2>&1 && command -v powershell >/dev/null 2>&1; then
  echo "[setup] Pruefe/Installiere Build Tools (winget)..."
  powershell -NoProfile -Command "
    $cl = Get-Command cl.exe -ErrorAction SilentlyContinue;
    if (-not $cl) {
      Write-Host '[setup] Microsoft C++ Build Tools nicht gefunden. Starte winget-Installation...' -ForegroundColor Yellow;
      $pkg = 'Microsoft.VisualStudio.2022.BuildTools';
      $args = '--override', '--passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --includeOptional';
      if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id $pkg --silent --accept-package-agreements --accept-source-agreements @args;
      } else {
        Write-Host '[setup] winget nicht verfuegbar. Lade Offline-Installer...' -ForegroundColor Red;
        $url = 'https://aka.ms/vs/17/release/vs_BuildTools.exe';
        $tmp = Join-Path $env:TEMP 'vs_BuildTools.exe';
        Invoke-WebRequest $url -OutFile $tmp;
        Start-Process -FilePath $tmp -ArgumentList '--passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --includeOptional' -Wait;
      }
    }
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe';
    if (Test-Path $vswhere) {
      $inst = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath;
      if ($inst) {
        $devcmd = Join-Path $inst 'Common7/Tools/VsDevCmd.bat';
        if (Test-Path $devcmd) {
          cmd.exe /c `"`"$devcmd`" -startdir=none -arch=x64 -host_arch=x64 && set`" | Out-File -FilePath $env:TEMP/msvc_env.txt -Encoding ascii;
        }
      }
    }
  "
  MSVC_ENV="${TEMP:-/tmp}/msvc_env.txt"
  if [ -f "$MSVC_ENV" ] 2>/dev/null; then
    while IFS='=' read -r name value; do
      export "$name"="$value"
    done < "$MSVC_ENV"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3.11 >/dev/null 2>&1; then
    PY_CMD="python3.11"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[run] Fehler: Python 3.11+ nicht gefunden."
    exit 1
fi

echo "[run] Starte Bootstrap (Installation + Launch)..."
"$PY_CMD" bootstrap.py --run "$@"

echo "[run] Vorgang abgeschlossen."
