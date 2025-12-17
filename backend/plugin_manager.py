"""Plugin Manager for JARVIS Core"""
import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

class PluginManager:
    """Manages plugins for JARVIS Core"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.root = Path.cwd()  # Current working directory
        self.plugins_dir = self.root / plugins_dir
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.enabled_plugins: Dict[str, bool] = {}
        self.config_file = self.root / "config" / "plugins.json"
        
        print(f"[INFO] Plugin Manager initialized")
        print(f"[INFO] Looking for plugins in: {self.plugins_dir}")
        
        # Load plugin states
        self._load_config()
        
        # Discover plugins
        self.discover_plugins()
    
    def _load_config(self):
        """Load plugin configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Ensure config is a dict
                    if isinstance(config, dict):
                        self.enabled_plugins = config.get('enabled', {})
                        # Ensure enabled_plugins is a dict
                        if not isinstance(self.enabled_plugins, dict):
                            print(f"[WARNING] Invalid enabled_plugins format, resetting")
                            self.enabled_plugins = {}
                    else:
                        print(f"[WARNING] Invalid config format, expected dict")
                        self.enabled_plugins = {}
                print(f"[INFO] Loaded plugin config from {self.config_file}")
            except Exception as e:
                print(f"[WARNING] Failed to load plugin config: {e}")
                self.enabled_plugins = {}
        else:
            print(f"[INFO] No plugin config found, starting fresh")
            self.enabled_plugins = {}
    
    def _save_config(self):
        """Save plugin configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'enabled': self.enabled_plugins}, f, indent=2)
            print(f"[INFO] Saved plugin config to {self.config_file}")
        except Exception as e:
            print(f"[ERROR] Failed to save plugin config: {e}")
    
    def discover_plugins(self):
        """Discover all available plugins in plugins directory"""
        if not self.plugins_dir.exists():
            print(f"[WARNING] Plugins directory not found: {self.plugins_dir}")
            print(f"[INFO] No plugins will be loaded")
            return
        
        print(f"[INFO] Discovering plugins in {self.plugins_dir}...")
        
        # Add plugins directory to path if not already there
        plugins_path_str = str(self.plugins_dir.absolute())
        if plugins_path_str not in sys.path:
            sys.path.insert(0, plugins_path_str)
            print(f"[INFO] Added {plugins_path_str} to Python path")
        
        # Scan for plugin files
        plugin_files = list(self.plugins_dir.glob("*_plugin.py"))
        print(f"[INFO] Found {len(plugin_files)} plugin files")
        
        for file in plugin_files:
            plugin_id = file.stem  # filename without .py
            
            try:
                # Import module
                module = importlib.import_module(plugin_id)
                
                # Extract plugin info
                plugin_info = self._extract_plugin_info(plugin_id, module)
                
                if plugin_info:
                    self.plugins[plugin_id] = plugin_info
                    print(f"[INFO] ✓ Discovered plugin: {plugin_info['name']} (v{plugin_info['version']})")
                    
            except Exception as e:
                print(f"[WARNING] ✗ Failed to load plugin {plugin_id}: {e}")
        
        print(f"[INFO] Successfully loaded {len(self.plugins)} plugins")
    
    def _extract_plugin_info(self, plugin_id: str, module) -> Optional[Dict[str, Any]]:
        """Extract plugin information from module"""
        # Look for plugin metadata
        name = getattr(module, 'PLUGIN_NAME', plugin_id.replace('_', ' ').title())
        description = getattr(module, 'PLUGIN_DESCRIPTION', 'No description available')
        version = getattr(module, 'PLUGIN_VERSION', '1.0.0')
        author = getattr(module, 'PLUGIN_AUTHOR', 'Unknown')
        
        # Check if plugin has required methods
        has_process = hasattr(module, 'process') or any(
            inspect.isclass(obj) and hasattr(obj, 'process')
            for name, obj in inspect.getmembers(module)
        )
        
        return {
            'id': plugin_id,
            'name': name,
            'description': description,
            'version': version,
            'author': author,
            'enabled': self.enabled_plugins.get(plugin_id, False),
            'status': 'available' if has_process else 'incomplete',
            'module': module
        }
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get list of all discovered plugins"""
        return [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description'],
                'version': p['version'],
                'author': p['author'],
                'enabled': p['enabled'],
                'status': p['status']
            }
            for p in self.plugins.values()
        ]
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get specific plugin info"""
        return self.plugins.get(plugin_id)
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        if plugin_id not in self.plugins:
            print(f"[ERROR] Plugin not found: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        if plugin['status'] != 'available':
            print(f"[ERROR] Plugin not available: {plugin_id}")
            return False
        
        # Enable plugin
        plugin['enabled'] = True
        self.enabled_plugins[plugin_id] = True
        self._save_config()
        
        print(f"[INFO] Enabled plugin: {plugin['name']}")
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id not in self.plugins:
            print(f"[ERROR] Plugin not found: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # Disable plugin
        plugin['enabled'] = False
        self.enabled_plugins[plugin_id] = False
        self._save_config()
        
        print(f"[INFO] Disabled plugin: {plugin['name']}")
        return True
    
    def get_enabled_plugins(self) -> List[Dict[str, Any]]:
        """Get list of enabled plugins"""
        return [
            p for p in self.plugins.values()
            if p['enabled']
        ]
    
    def reload_plugins(self):
        """Reload all plugins (hot-reload)"""
        print("[INFO] Reloading plugins...")
        self.plugins.clear()
        self.discover_plugins()
        print(f"[INFO] Reloaded {len(self.plugins)} plugins")

# Global plugin manager instance
print("[INFO] Initializing global plugin manager...")
plugin_manager = PluginManager()
print(f"[INFO] Plugin manager ready with {len(plugin_manager.plugins)} plugins")

if __name__ == "__main__":
    # Test plugin discovery
    print("\nPlugin Manager Test")
    print("="*50)
    
    plugins = plugin_manager.get_all_plugins()
    print(f"\nFound {len(plugins)} plugins:\n")
    
    for plugin in plugins:
        status_icon = "✓" if plugin['enabled'] else "✗"
        print(f"{status_icon} {plugin['name']} (v{plugin['version']})")
        print(f"  ID: {plugin['id']}")
        print(f"  Description: {plugin['description']}")
        print(f"  Status: {plugin['status']}")
        print()
