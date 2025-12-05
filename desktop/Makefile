.PHONY: help install dev build clean

help:
	@echo "J.A.R.V.I.S. Desktop - Makefile"
	@echo ""
	@echo "Verfügbare Targets:"
	@echo "  install    - Abhängigkeiten installieren"
	@echo "  dev        - Development starten"
	@echo "  build      - Production Build"
	@echo "  clean      - Build-Artefakte löschen"

install:
	@echo "📦 Installiere Abhängigkeiten..."
	cd frontend && npm install
	cd backend && go mod download
	@echo "✅ Fertig!"

dev:
	@echo "🚀 Starte Dev Mode..."
	wails dev

build:
	@echo "🔨 Baue Production Binary..."
	cd frontend && npm run build
	wails build -clean
	@echo "✅ Build fertig! Binary: ./build/bin/jarvis-desktop"

clean:
	@echo "🧹 Räume auf..."
	rm -rf build/
	rm -rf frontend/dist/
	@echo "✅ Fertig!"

build-windows:
	wails build -clean -platform windows/amd64

build-linux:
	wails build -clean -platform linux/amd64

build-macos:
	wails build -clean -platform darwin/universal
