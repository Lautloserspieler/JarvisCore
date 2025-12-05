@echo off
echo 🚀 Starting J.A.R.V.I.S. Desktop Dev Mode...

echo ⚠️ Stelle sicher, dass JarvisCore läuft (python main.py)
echo.

timeout /t 3 /nobreak

cd desktop
wails dev
