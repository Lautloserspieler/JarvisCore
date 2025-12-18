# 🧪 Testing Quick Start

## TL;DR - Run All Tests

### Linux/Mac
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Windows
```cmd
run_tests.bat
```

---

## Installation

### Backend Testing Setup
```bash
cd backend
pip install -r requirements-dev.txt
```

### Frontend Testing Setup
```bash
cd frontend
npm install
```

---

## Quick Commands

### Backend (pytest)
```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov              # With coverage
pytest tests/test_plugin_manager.py  # Single file
```

### Frontend (vitest)
```bash
cd frontend
npm run test              # Watch mode
npm run test:run          # Run once
npm run test:ui           # UI mode
npm run test:coverage     # With coverage
```

---

## What Gets Tested?

### Backend ✅
- ✅ Plugin Manager (enable/disable/list)
- ✅ Settings Management (load/save/validate)
- ✅ API Endpoints (structure validation)
- ✅ Model Downloader (URL validation, checksums)

### Frontend ✅
- ✅ Vue Components (ChatTab, PluginsTab)
- ✅ i18n Translations (key matching, completeness)
- ✅ Component rendering
- ✅ User interactions

---

## Coverage Reports

After running tests with coverage:

**Backend**: Open `backend/htmlcov/index.html`
**Frontend**: Open `frontend/coverage/index.html`

---

## CI/CD

Tests run automatically on:
- ✅ Push to `main` or `develop`
- ✅ Pull requests
- ✅ Manual trigger

View results: [GitHub Actions](https://github.com/Lautloserspieler/JarvisCore/actions)

---

## Need Help?

See full documentation: [docs/TESTING.md](./TESTING.md)
