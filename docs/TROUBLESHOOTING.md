# 🔧 JARVIS Troubleshooting Guide

## Häufige Probleme & Lösungen

---

## ❌ `ModuleNotFoundError: No module named 'numpy'`

### Problem
Pakete wurden **global** installiert statt in der **venv**.

### Lösung

```powershell
# 1. Aktiviere venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Installiere Pakete in venv
pip install -r requirements.txt

# 3. Starte JARVIS
python main.py
```

### Schnell-Fix

```powershell
# In aktivierter venv:
python scripts/quick_fix_venv.py
```

---

## ⚠️ `geopandas requires pandas>=2.0.0, but you have pandas 1.5.3`

### Problem
Pandas Version-Konflikt zwischen requirements.txt und installierten Paketen.

### Lösung

```powershell
# Option 1: Quick Fix
python scripts/fix_pandas_conflict.py

# Option 2: Manuell
pip uninstall -y pandas
pip install "pandas>=2.0.0,<3.0"
```

---

## 📦 Setup.py installiert Pakete außerhalb der venv

### Problem
`setup.py` hat `capture_output=True`, was dazu führt, dass pip im globalen Python läuft.

### Lösung

```powershell
# 1. Lösche alte venv
Remove-Item -Recurse -Force venv

# 2. Hole neuestes setup.py
git pull origin main

# 3. Setup neu laufen lassen
python setup.py
```

**Oder:**

```powershell
# Manuelles Setup
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔴 Venv existiert, aber ist leer

### Symptom
```
⚠️  Virtuelle Umgebung existiert bereits (venv/)
```

### Lösung

```powershell
# Lösche und neu erstellen
Remove-Item -Recurse -Force venv
python setup.py
```

---

## ❌ `ImportError` bei JARVIS Start

### Checkliste

1. **Venv aktiviert?**
   ```powershell
   # Prompt sollte (venv) zeigen
   (venv) PS C:\...> 
   ```

2. **Numpy installiert?**
   ```powershell
   pip show numpy
   ```

3. **Requirements installiert?**
   ```powershell
   pip list | Select-String "pandas|numpy|torch"
   ```

4. **Python-Version korrekt?**
   ```powershell
   python --version
   # Sollte 3.11+ sein
   ```

---

## 💡 Komplette Neu-Installation

```powershell
# 1. Backup (optional)
cp -r data data_backup

# 2. Clean install
Remove-Item -Recurse -Force venv
Remove-Item -Recurse -Force __pycache__

# 3. Setup
python setup.py

# 4. Aktiviere venv
venv\Scripts\activate

# 5. Verifiziere
pip list

# 6. Start
python main.py
```

---

## 🤖 JARVIS startet nicht

### Logs checken

```powershell
# Log-Datei öffnen
cat logs/jarvis.log

# Letzte 50 Zeilen
Get-Content logs/jarvis.log -Tail 50
```

### Test-Modus

```powershell
# Minimaler Start (ohne UI)
python -c "from core.jarvis import JarvisAssistant; j = JarvisAssistant(); print('OK')"
```

---

## 🐛 Debug-Modus aktivieren

**data/settings.json:**
```json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

**Oder via ENV:**
```powershell
$env:JARVIS_DEBUG = "1"
python main.py
```

---

## 📧 Support

**Problem nicht gelöst?**

1. **Issue erstellen:** https://github.com/Lautloserspieler/JarvisCore/issues
2. **Discord:** (falls vorhanden)
3. **Logs mitschicken:** `logs/jarvis.log`

**Info sammeln:**
```powershell
# System Info
python --version
pip --version
pip list > installed_packages.txt

# JARVIS Info
python -c "import sys; print(sys.prefix)"
```

---

## ✅ Prüfung nach Fix

```powershell
# 1. Venv aktiv?
echo $env:VIRTUAL_ENV

# 2. Pakete vorhanden?
pip show numpy pandas torch fastapi

# 3. Import-Test
python -c "import numpy, pandas, torch, fastapi; print('✅ All OK')"

# 4. JARVIS Start
python main.py
```

---

**Aktualisiert:** 2025-12-10
