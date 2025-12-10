# ⚠️ DEPRECATED - Old Desktop UI

**Status:** 🔴 Deprecated  
**Date:** 2025-12-10  
**Replacement:** Web UI at `/frontend`

---

## This folder is deprecated!

The **DearPyGui/ImGui Desktop UI** in this folder is **no longer maintained** and will be **removed soon**.

### ✅ Use the new Web UI instead:

```bash
# Start JARVIS with Web UI
python main_web.py

# Open browser
http://localhost:8000
```

### Migration Guide

**Old Desktop UI:**
- `desktop/jarvis_imgui_app_full.py` ❌
- DearPyGui dependency ❌
- Windows-only ❌

**New Web UI:**
- `frontend/` (React + TypeScript) ✅
- FastAPI backend ✅
- Cross-platform ✅
- Mobile-friendly ✅
- Remote access ✅

### Features Comparison

| Feature | Old Desktop UI | New Web UI |
|---------|---------------|------------|
| **Platform** | Windows only | All platforms |
| **Access** | Local only | Remote capable |
| **Tech** | DearPyGui/ImGui | React + FastAPI |
| **Design** | Basic | JARVIS futuristic theme |
| **Mobile** | No | Yes (responsive) |
| **Updates** | Manual restart | Live reload |
| **API** | None | REST + WebSocket |

### Timeline

- **2025-12-10:** Web UI released, Desktop UI deprecated
- **2025-12-15:** Desktop UI will be removed from main branch
- **Archive:** Old UI moved to `archive/desktop-ui-legacy/`

### Need the old UI?

Checkout an older commit:

```bash
git checkout <commit-before-removal>
cd desktop
python jarvis_imgui_app_full.py
```

---

**Questions?** Open an issue: https://github.com/Lautloserspieler/JarvisCore/issues
