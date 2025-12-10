#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Example: How to integrate Enhanced Model Manager into jarvis_imgui_app_full.py

This file shows the minimal changes needed to replace the existing Models tab
with the enhanced version.
"""

# ============================================================================
# STEP 1: Add import at the top of jarvis_imgui_app_full.py
# ============================================================================

from desktop.model_manager_ui import ExtendedModelManagerUI


# ============================================================================
# STEP 2: Initialize in __init__ method of JarvisUE5ControlCenter
# ============================================================================

class JarvisUE5ControlCenter:
    def __init__(self, jarvis_instance=None):
        # ... existing initialization ...
        
        # Add this line after self.jarvis = jarvis_instance
        self.enhanced_model_manager = ExtendedModelManagerUI(jarvis_instance)
        
        # ... rest of initialization ...


# ============================================================================
# STEP 3: Replace _build_models method OR modify tab creation
# ============================================================================

# Option A: Replace the entire _build_models method
def _build_models(self):
    """Build enhanced model manager tab"""
    self.enhanced_model_manager.build_ui(dpg.last_container())


# Option B: Modify the tab creation in _create_ui
def _create_ui(self):
    with dpg.window(label="JARVIS", tag="main", no_close=True, no_collapse=True):
        # ... header code ...
        
        with dpg.tab_bar():
            with dpg.tab(label="  📊 Dashboard  "): 
                self._build_dashboard()
            
            with dpg.tab(label="  💬 Chat  "): 
                self._build_chat()
            
            # REPLACE THIS:
            # with dpg.tab(label="  🧠 Models  "): 
            #     self._build_models()
            
            # WITH THIS:
            with dpg.tab(label="  🧠 Models  "):
                self.enhanced_model_manager.build_ui(dpg.last_container())
            
            # ... rest of tabs ...


# ============================================================================
# COMPLETE EXAMPLE: Modified jarvis_imgui_app_full.py
# ============================================================================

"""
Full example showing all modifications in context:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dearpygui.dearpygui as dpg
from desktop.model_manager_ui import ExtendedModelManagerUI  # NEW

class JarvisUE5ControlCenter:
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance
        self.is_running = True
        
        # NEW: Initialize enhanced model manager
        self.enhanced_model_manager = ExtendedModelManagerUI(jarvis_instance)
        
        # ... existing initialization ...
        
        self._init_context()
        self._setup_fonts()
        self._apply_ue5_theme()
        self._create_ui()
        self._start_background_workers()
    
    def _create_ui(self):
        with dpg.window(label="JARVIS", tag="main", no_close=True, no_collapse=True):
            # ... header ...
            
            with dpg.tab_bar():
                with dpg.tab(label="  📊 Dashboard  "): 
                    self._build_dashboard()
                
                with dpg.tab(label="  💬 Chat  "): 
                    self._build_chat()
                
                # MODIFIED: Use enhanced model manager
                with dpg.tab(label="  🧠 Models  "):
                    self.enhanced_model_manager.build_ui(dpg.last_container())
                
                with dpg.tab(label="  🧩 Plugins  "): 
                    self._build_plugins()
                
                with dpg.tab(label="  🗄️ Memory  "): 
                    self._build_memory()
                
                with dpg.tab(label="  📜 Logs  "): 
                    self._build_logs()
                
                with dpg.tab(label="  ⚙️ Settings  "): 
                    self._build_settings()
            
            # ... footer ...
    
    # REMOVED: Old _build_models method
    # def _build_models(self):
    #     # ... old code ...
    
    # ... rest of class ...
```
"""


# ============================================================================
# VERIFICATION: Test the integration
# ============================================================================

def verify_integration():
    """
    Run this to verify the integration works correctly
    """
    print("Verifying Enhanced Model Manager integration...")
    
    # Check imports
    try:
        from desktop.model_manager_ui import ExtendedModelManagerUI
        from desktop.model_manager_extended import ModelBenchmark, ModelDownloadManager
        print("✅ Imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check if files exist
    import os
    files = [
        'desktop/model_manager_extended.py',
        'desktop/model_manager_ui.py',
        'desktop/INTEGRATION_EXAMPLE.py',
        'docs/ENHANCED_MODEL_MANAGER.md'
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    print("\n✅ All checks passed!")
    print("\nNext steps:")
    print("1. Modify desktop/jarvis_imgui_app_full.py as shown above")
    print("2. Run: python main.py")
    print("3. Navigate to the Models tab")
    print("4. Test download, benchmark, and comparison features")
    
    return True


if __name__ == "__main__":
    verify_integration()
