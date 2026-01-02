# Architecture Refactoring Plan v1.2

**Status:** 🟡 In Planning  
**Target Release:** v1.2.0 (post v1.1.0)  
**Last Updated:** 2025-12-26

---

## Executive Summary

This document addresses critical architectural inconsistencies identified in JarvisCore that could impact:
- Developer onboarding experience
- System stability and maintainability
- Production deployment reliability
- Community contribution quality

---

## 1. Entry Points Clarification

### Current State ❌

**Two competing entry points:**
- `main.py` (root) → Web mode (FastAPI + Vite dev server)
- `scripts/start_jarvis.py` → Desktop mode (Wails app)

**Problem:** No clear documentation which is "the default" or when to use which.

### Target State ✅

```
JarvisCore/
├── main.py                    # 🌐 DEFAULT: Web Development Mode
├── scripts/
│   ├── start_web.py          # Explicit web mode launcher
│   ├── start_desktop.py      # Desktop mode (Wails)
│   └── start_production.py   # Production deployment
└── README.md                  # Clear mode explanation
```

### Implementation Plan

1. **Rename/Restructure Entry Points**
   - `main.py` → Keep as default (web dev mode)
   - `scripts/start_jarvis.py` → `scripts/start_desktop.py`
   - Create `scripts/start_web.py` (delegates to `main.py` with clear messaging)
   - Create `scripts/start_production.py` (optimized production config)

2. **Update Documentation**
   - README.md: Add "Getting Started" section with mode decision tree
   - ./DEPLOYMENT.md: Separate sections for Web vs Desktop deployment
   - Add `docs/modes.md` explaining:
     - Web Mode: Development, browser-based UI
     - Desktop Mode: Packaged Wails app, native UI
     - Production Mode: Optimized for server deployment

3. **CLI Improvements**
   ```bash
   # Clear, explicit commands
   python -m jarviscore web      # Web dev mode
   python -m jarviscore desktop  # Desktop mode
   python -m jarviscore prod     # Production mode
   ```

---

## 2. Dependency Management Consolidation

### Current State ❌

**Multiple dependency sources:**
- `pyproject.toml` (root)
- `requirements.txt` (root)
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/requirements-ci.txt`

**Problem:** Version conflicts, unclear installation path, contributor confusion.

### Target State ✅

**Single Source of Truth: `pyproject.toml`**

```toml
[project]
name = "jarviscore"
version = "1.2.0"
dependencies = [
    "fastapi[all]>=0.115.0",
    "torch>=2.0.0",
    "transformers>=4.35.0",
    # ... all runtime deps
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
ci = [
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
]
tts = [
    "TTS>=0.22.0",
    "pyttsx3>=2.90",
]
cuda = [
    "torch[cuda]>=2.0.0",
]
```

### Implementation Plan

1. **Audit All Dependencies**
   ```bash
   # Generate consolidated list
   pip-compile pyproject.toml --extra dev --extra tts
   ```

2. **Migration Strategy**
   - Week 1: Consolidate into `pyproject.toml`
   - Week 2: Deprecate old `requirements.txt` files (keep as legacy reference)
   - Week 3: Update CI/CD to use `pip install -e ".[dev,ci]"`

3. **Installation Simplification**
   ```bash
   # Standard install
   pip install -e .
   
   # With TTS support
   pip install -e ".[tts]"
   
   # Development setup
   pip install -e ".[dev,tts]"
   
   # Full CI setup
   pip install -e ".[dev,ci,tts]"
   ```

---

## 3. Go Services Strategy

### Current State ❌

**Two parallel Go implementations:**
- `go/cmd/` → Service daemons (gatewayd, memoryd, etc.)
- `go-services/` → Monorepo-style services

**Problem:** Unclear which is active, code duplication, wasted effort.

### Target State ✅

**Single Go Structure**

```
go/
├── cmd/                 # Service entry points
│   ├── gatewayd/
│   ├── memoryd/
│   └── securityd/
├── internal/            # Shared internal packages
│   ├── auth/
│   ├── database/
│   └── grpc/
├── pkg/                 # Public reusable packages
└── scripts/             # Build and deployment scripts
```

### Implementation Plan

1. **Decision: Which Go Structure to Keep?**
   - **Recommendation:** Keep `go/cmd/` (more idiomatic Go structure)
   - Move useful code from `go-services/` into `go/internal/`
   - Archive `go-services/` to `archive/go-services-legacy/`

2. **Mark Legacy Code**
   ```
   archive/
   └── go-services-legacy/
       └── README.md  # Explanation: deprecated, use go/ instead
   ```

3. **Update Documentation**
   - `docs/architecture/go-services.md` → Clear service architecture
   - Build instructions in `go/README.md`

---

## 4. Plugin System Improvements

### Current State ⚠️

**Working but fragile:**
- Import-time initialization (can crash backend)
- Missing API keys = silent failures
- No centralized plugin registry UI
- HTTP URLs instead of HTTPS (security risk)

### Target State ✅

1. **Lazy Plugin Loading**
   ```python
   # backend/main.py
   @app.on_event("startup")
   async def startup():
       plugin_manager = PluginManager()
       await plugin_manager.load_all_async()  # Isolated failures
   ```

2. **Plugin Health Checks**
   ```python
   class Plugin:
       async def health_check(self) -> PluginHealth:
           return PluginHealth(
               status="healthy" | "degraded" | "unhealthy",
               missing_config=["OPENWEATHER_API_KEY"],
               errors=["API timeout"]
           )
   ```

3. **Plugin Registry UI**
   - Frontend page: `/plugins` showing:
     - Active plugins
     - Required config (missing keys highlighted)
     - Enable/disable toggles
     - Health status indicators

### Implementation Plan

1. **Week 1: Plugin Manager Refactor**
   - Move plugin init to FastAPI `startup` event
   - Add error isolation (try/except per plugin)
   - Add plugin health check interface

2. **Week 2: Frontend Registry**
   - Create `PluginRegistry.vue` component
   - Add API endpoint: `GET /api/plugins/status`
   - Show missing config with setup instructions

3. **Week 3: Security Fixes**
   - Weather plugin: Change `http://` → `https://`
   - Audit all plugins for security issues
   - Add HTTPS validation in plugin loader

---

## 5. Environment Configuration

### Current State ❌

**Minimal `.env.example`:**
```env
# Only 3 variables documented
JARVIS_BACKEND_PORT=5050
JARVIS_FRONTEND_PORT=5000
JARVIS_LOG_LEVEL=INFO
```

### Target State ✅

**Comprehensive `.env.example`:**
```env
# === Core System ===
JARVIS_BACKEND_PORT=5050
JARVIS_FRONTEND_PORT=5000
JARVIS_LOG_LEVEL=INFO
JARVIS_MODE=development  # development | production | desktop

# === LLM Configuration ===
LLM_DEFAULT_MODEL=llama32-3b
LLM_CONTEXT_SIZE=8192
LLM_GPU_LAYERS=-1  # -1 = auto, 0 = CPU only

# === TTS Configuration ===
TTS_ENGINE=xtts  # xtts | pyttsx3
TTS_DEVICE=cuda  # cuda | cpu
TTS_LANGUAGE=de

# === Plugin API Keys ===
OPENWEATHER_API_KEY=your_key_here
NEWS_API_KEY=your_key_here

# === Feature Flags ===
ENABLE_VOICE_CONTROL=true
ENABLE_DESKTOP_NOTIFICATIONS=true
ENABLE_TELEMETRY=false

# === Database (Future) ===
# DATABASE_URL=sqlite:///data/jarvis.db
```

---

## 6. CI/CD Quality Gates

### Current State ⚠️

**Tests run but often pass with `|| true` (soft failures)**

### Target State ✅

**Strict Quality Gates**

```yaml
# .github/workflows/quality.yml
name: Quality Gate
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff black
      - run: ruff check .  # MUST pass
      - run: black --check .  # MUST pass

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev,ci]"
      - run: pytest --cov=backend --cov-fail-under=70  # 70% coverage required

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r backend/
      - run: safety check
```

### Implementation Plan

1. **Phase 1: Baseline (No Breaking Changes)**
   - Run tests, allow failures, collect metrics
   - Identify flaky tests

2. **Phase 2: Incremental Strictness**
   - Week 1: Enforce linting (ruff/black)
   - Week 2: Require 50% test coverage
   - Week 3: Require 70% test coverage

3. **Phase 3: Production Ready**
   - Security scans (bandit, safety)
   - Dependency vulnerability checks
   - License compliance

---

## 7. Migration Timeline

### Phase 1: Foundation (Weeks 1-2) 🟢 **PRIORITY**

- [ ] Consolidate dependencies → `pyproject.toml`
- [ ] Clarify entry points → Rename scripts
- [ ] Update README with clear "Getting Started"
- [ ] Expand `.env.example`

### Phase 2: Cleanup (Weeks 3-4) 🟡

- [ ] Archive legacy Go services
- [ ] Plugin lazy loading
- [ ] Plugin health checks
- [ ] Security fixes (HTTPS)

### Phase 3: Quality (Weeks 5-6) 🟡

- [ ] CI/CD quality gates
- [ ] Test coverage improvement
- [ ] Plugin registry UI

### Phase 4: Documentation (Week 7) 🟢

- [ ] Architecture docs
- [ ] API documentation
- [ ] Deployment guides
- [ ] Contributor onboarding

---

## 8. Breaking Changes & Migration Guide

### For Users

**Before (v1.1):**
```bash
pip install -r requirements.txt
python main.py
```

**After (v1.2):**
```bash
pip install -e ".[tts]"  # or just: pip install -e .
python -m jarviscore web  # explicit mode
```

### For Contributors

**Before:**
- Unclear which `requirements.txt` to use
- No clear test requirements

**After:**
```bash
pip install -e ".[dev,ci]"  # Everything needed
pytest  # Runs with coverage
ruff check .  # Must pass
```

---

## 9. Success Metrics

- ✅ **Onboarding Time:** New contributor can run system < 5 minutes
- ✅ **Build Success Rate:** CI builds pass > 95%
- ✅ **Test Coverage:** Backend coverage > 70%
- ✅ **Documentation:** All major features documented
- ✅ **Security:** Zero high-severity vulnerabilities

---

## 10. Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Use `pyproject.toml` as single source | Modern Python standard, better tooling support | 2025-12-26 |
| Keep `go/cmd/` structure | More idiomatic Go, better tooling | 2025-12-26 |
| Default to Web mode | Lower barrier to entry, easier debugging | 2025-12-26 |
| Lazy plugin loading | Prevents startup crashes, better error isolation | 2025-12-26 |

---

## Next Steps

1. **Review this document** with core team
2. **Create GitHub Project** for tracking
3. **Start Phase 1** (Foundation) immediately
4. **Weekly sync** to track progress

**Questions?** Open an issue with label `architecture-refactor`
