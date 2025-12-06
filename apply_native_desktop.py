#!/usr/bin/env python3
"""Patch-Script für native Desktop-UI in main.py"""

import re
from pathlib import Path

# Lese main.py
main_path = Path("main.py")
main_content = main_path.read_text(encoding="utf-8")

# 1. Füge Import für native Desktop-App hinzu
import_block = """# Lokale Imports
from core.speech_recognition import SpeechRecognizer"""

new_import_block = """# Lokale Imports
try:
    from desktop.jarvis_desktop_app import create_jarvis_desktop_gui
    NATIVE_DESKTOP_AVAILABLE = True
except ImportError:
    NATIVE_DESKTOP_AVAILABLE = False
    
from core.speech_recognition import SpeechRecognizer"""

main_content = main_content.replace(import_block, new_import_block)

# 2. Ersetze _initialise_gui Methode
old_gui_init = r'def _initialise_gui\(self\):.*?return WebInterfaceBridge\(self, self\.logger\)'

new_gui_init = '''def _initialise_gui(self):
        """Initialisiert die Desktop- oder Web-UI."""
        try:
            desktop_cfg = self.settings.get('desktop_app', {}) or {}
        except Exception:
            desktop_cfg = {}
            
        self._desktop_cfg = desktop_cfg if isinstance(desktop_cfg, dict) else {}
        self.desktop_app_enabled = bool(self._desktop_cfg.get("enabled") or os.getenv("JARVIS_DESKTOP"))
        
        # NATIVE DESKTOP APP (PyQt6)
        if self.desktop_app_enabled and NATIVE_DESKTOP_AVAILABLE:
            try:
                self.logger.info("Native Desktop-App wird initialisiert...")
                gui = create_jarvis_desktop_gui(self)
                return gui
            except Exception as exc:
                self.logger.warning("Native Desktop-App konnte nicht geladen werden: %s", exc)
        
        # Fallback: Web-Bridge
        self.logger.info("Desktop-GUI deaktiviert. Weboberfläche übernimmt die Visualisierung.")
        return WebInterfaceBridge(self, self.logger)'''

main_content = re.sub(old_gui_init, new_gui_init, main_content, flags=re.DOTALL)

# Schreibe zurück
main_path.write_text(main_content, encoding="utf-8")

print("✅ main.py wurde gepatcht!")
print("✅ Native Desktop-App ist jetzt integriert")
print("")
print("🚀 Installation:")
print("   pip install PyQt6")
print("")
print("🚀 Starten:")
print("   python main.py")
