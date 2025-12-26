# Migration Guide: v1.1 → v1.2

**Last Updated:** 2025-12-26  
**Target Version:** v1.2.0-dev

---

## Overview

Version 1.2 introduces significant architectural improvements:
- ✅ Consolidated dependency management
- ✅ Modern CLI with mode selection
- ✅ Improved configuration system
- ✅ Better plugin isolation

**Estimated Migration Time:** 5-10 minutes

---

## Breaking Changes

### 1. Installation Method

**Before (v1.1):**
```bash
pip install -r requirements.txt
```

**After (v1.2):**
```bash
# Standard installation
pip install -e ".[tts]"

# Development setup
pip install -e ".[dev,tts]"

# Full installation (all features)
pip install -e ".[all]"
```

### 2. Startup Command

**Before (v1.1):**
```bash
python main.py
```

**After (v1.2):**
```bash
# Explicit mode selection
jarviscore web      # Web development mode (default)
jarviscore desktop  # Desktop mode (future)
jarviscore prod     # Production mode (future)

# OR: Old method still works
python main.py
```

### 3. Configuration

**New `.env` variables available:**
- See `.env.example` for complete list
- Old variables still supported (backward compatible)

---

## Step-by-Step Migration

### Step 1: Backup Current Installation

```bash
# Save your current .env file
cp .env .env.backup

# Save your plugin configurations
cp -r plugins plugins.backup
```

### Step 2: Update Repository

```bash
git pull origin main
```

### Step 3: Clean Old Environment

```bash
# Deactivate current environment
deactivate

# Remove old environment (optional but recommended)
rm -rf venv/  # or .venv/

# Create fresh environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Step 4: Install New Dependencies

```bash
# Standard installation (with TTS)
pip install -e ".[tts]"

# OR: Full installation
pip install -e ".[all]"
```

### Step 5: Update Configuration

```bash
# Copy new .env.example
cp .env.example .env

# Merge your old settings from .env.backup
# Important variables to copy:
# - OPENWEATHER_API_KEY
# - NEWS_API_KEY
# - Any custom ports or settings
```

### Step 6: Test Installation

```bash
# Test CLI
jarviscore --help

# Start in web mode
jarviscore web

# OR: Use old method
python main.py
```

---

## What Changed?

### Dependency Management

| What | Before (v1.1) | After (v1.2) |
|------|---------------|---------------|
| **Source of Truth** | Multiple `requirements.txt` | Single `pyproject.toml` |
| **Installation** | `pip install -r requirements.txt` | `pip install -e ".[tts]"` |
| **Dev Tools** | Manual install | `pip install -e ".[dev]"` |
| **Optional Features** | Always installed | Choose: `[tts]`, `[cuda]`, `[desktop]` |

### CLI & Startup

| What | Before (v1.1) | After (v1.2) |
|------|---------------|---------------|
| **Command** | `python main.py` | `jarviscore web` |
| **Mode Selection** | Not explicit | Explicit: `web`/`desktop`/`prod` |
| **Help** | README only | `jarviscore --help` |

### Configuration

| What | Before (v1.1) | After (v1.2) |
|------|---------------|---------------|
| **Variables** | ~5 documented | ~50 documented |
| **Examples** | Minimal | Comprehensive `.env.example` |
| **Validation** | None | Coming soon |

---

## Troubleshooting

### Problem: `pip install -e .` fails

**Cause:** Missing build dependencies

**Solution:**
```bash
pip install --upgrade pip setuptools wheel
pip install -e ".[tts]"
```

### Problem: `jarviscore` command not found

**Cause:** Package not installed in editable mode

**Solution:**
```bash
pip install -e .
# OR restart your terminal
```

### Problem: Import errors for specific modules

**Cause:** Optional dependencies not installed

**Solution:**
```bash
# Install all optional dependencies
pip install -e ".[all]"

# OR install specific extras
pip install -e ".[tts,cuda,desktop]"
```

### Problem: Old `requirements.txt` still referenced

**Cause:** CI/CD not updated

**Solution:**
Update your CI configuration:
```yaml
# Old
- pip install -r requirements.txt

# New
- pip install -e ".[dev,ci]"
```

---

## FAQ

### Q: Can I still use `requirements.txt`?

**A:** Yes, for backward compatibility. It now delegates to `pyproject.toml` via `-e .`

### Q: Do I need to reinstall everything?

**A:** Recommended, but not required. Old installations will mostly work.

### Q: What if I don't want TTS?

**A:** Install without `[tts]` extra:
```bash
pip install -e .  # Minimal install
```

### Q: What about CUDA support?

**A:** Install with CUDA extra:
```bash
pip install -e ".[cuda,tts]"  # PyTorch with CUDA
```

### Q: Will my plugins still work?

**A:** Yes, fully backward compatible. Plugins will be more stable due to lazy loading.

### Q: What happens to `backend/requirements.txt`?

**A:** Deprecated. Will be removed in v1.3.0.

---

## Rollback (If Needed)

```bash
# Checkout previous version
git checkout v1.1.0

# Reinstall old dependencies
pip install -r requirements.txt

# Restore old .env
mv .env.backup .env
```

---

## Next Steps After Migration

1. ✅ **Test Core Functionality**
   ```bash
   jarviscore web
   # Visit http://localhost:5000
   # Test chat, TTS, plugins
   ```

2. ✅ **Update Your Scripts**
   - Replace `python main.py` with `jarviscore web`
   - Update CI/CD pipelines
   - Update deployment scripts

3. ✅ **Configure New Features**
   - Check `.env.example` for new options
   - Enable/disable features via flags
   - Configure plugin API keys

4. ✅ **Review Documentation**
   - Read `ARCHITECTURE_REFACTOR.md`
   - Check plugin docs
   - Review security guidelines

---

## Support

Need help?
- 📖 [README](README.md)
- 🐛 [Issues](https://github.com/Lautloserspieler/JarvisCore/issues)
- 💬 [Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions)
- 📧 Email: emeyer@fn.de

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for complete list of changes in v1.2.
