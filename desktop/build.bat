@echo off
echo 🔨 Building J.A.R.V.I.S. Desktop...

echo 📦 Building Frontend...
cd frontend
call npm install
call npm run build
cd ..

echo 🔧 Building Go Backend...
wails build

echo ✅ Build abgeschlossen!
echo Binary: .\build\bin\jarvis-desktop.exe
pause
