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
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, plugins_dir: str = None):
        # Prevent re-initialization
        if self._initialized:
            return
        
        # If plugins_dir not specified, look in root
        if plugins_dir is None:
            # Find root directory (parent of backend)
            current = Path(__file__).parent  # backend dir
            self.root = current.parent  # root dir
            plugins_dir = "plugins"
        else:
            self.root = Path.cwd()
            
        self.plugins_dir = self.root / plugins_dir
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.enabled_plugins: Dict[str, bool] = {}
        self.config_file = self.root / "config" / "plugins.json"
        
        print(f"[PLUGINS] Initializing Plugin Manager...")
        print(f"[PLUGINS] Root: {self.root}")
        print(f"[PLUGINS] Looking for plugins in: {self.plugins_dir}")
        
        # Load plugin states
        self._load_config()
        
        # Discover plugins
        self.discover_plugins()
        
        self._initialized = True
        print(f"[PLUGINS] Plugin Manager ready with {len(self.plugins)} plugins")
    
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
                            print(f"[PLUGINS] Invalid enabled_plugins format, resetting")
                            self.enabled_plugins = {}
                    else:
                        print(f"[PLUGINS] Invalid config format, expected dict")
                        self.enabled_plugins = {}
                print(f"[PLUGINS] Loaded plugin config")
            except Exception as e:
                print(f"[PLUGINS] Failed to load config: {e}")
                self.enabled_plugins = {}
        else:
            self.enabled_plugins = {}
    
    def _save_config(self):
        """Save plugin configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'enabled': self.enabled_plugins}, f, indent=2)
        except Exception as e:
            print(f"[PLUGINS] Failed to save config: {e}")
    
    def discover_plugins(self):
        """Discover all available plugins in plugins directory"""
        if not self.plugins_dir.exists():
            print(f"[PLUGINS] Directory not found: {self.plugins_dir}")
            return
        
        print(f"[PLUGINS] Scanning directory...")
        
        # Add plugins directory to path if not already there
        plugins_path_str = str(self.plugins_dir.absolute())
        if plugins_path_str not in sys.path:
            sys.path.insert(0, plugins_path_str)
        
        # Scan for plugin files
        plugin_files = list(self.plugins_dir.glob("*_plugin.py"))
        print(f"[PLUGINS] Found {len(plugin_files)} plugin files")
        
        loaded_count = 0
        for file in plugin_files:
            plugin_id = file.stem  # filename without .py
            
            try:
                # Import module
                module = importlib.import_module(plugin_id)
                
                # Extract plugin info
                plugin_info = self._extract_plugin_info(plugin_id, module)
                
                if plugin_info:
                    self.plugins[plugin_id] = plugin_info
                    loaded_count += 1
                    print(f"[PLUGINS] ✓ {plugin_info['name']} (v{plugin_info['version']})")
                    
            except Exception as e:
                print(f"[PLUGINS] ✗ Failed: {plugin_id} - {e}")
        
        print(f"[PLUGINS] Loaded {loaded_count}/{len(plugin_files)} plugins")
    
    def _extract_plugin_info(self, plugin_id: str, module) -> Optional[Dict[str, Any]]:
        """Extract plugin information from module"""
        # Look for plugin metadata
        name = getattr(module, 'PLUGIN_NAME', plugin_id.replace('_', ' ').title())
        description = getattr(module, 'PLUGIN_DESCRIPTION', 'No description available')
        version = getattr(module, 'PLUGIN_VERSION', '1.0.0')
        author = getattr(module, 'PLUGIN_AUTHOR', 'Lautloserspieler')
        
        # All plugins are available
        return {
            'id': plugin_id,
            'name': name,
            'description': description,
            'version': version,
            'author': author,
            'enabled': self.enabled_plugins.get(plugin_id, False),
            'status': 'available',
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
            print(f"[PLUGINS] Not found: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # Enable plugin
        plugin['enabled'] = True
        self.enabled_plugins[plugin_id] = True
        self._save_config()
        
        print(f"[PLUGINS] Enabled: {plugin['name']}")
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        
        # Disable plugin
        plugin['enabled'] = False
        self.enabled_plugins[plugin_id] = False
        self._save_config()
        
        print(f"[PLUGINS] Disabled: {plugin['name']}")
        return True
    
    def get_enabled_plugins(self) -> List[Dict[str, Any]]:
        """Get list of enabled plugins"""
        return [
            p for p in self.plugins.values()
            if p['enabled']
        ]
    
    def reload_plugins(self):
        """Reload all plugins (hot-reload)"""
        print("[PLUGINS] Reloading...")
        self.plugins.clear()
        self.discover_plugins()

# Create singleton instance
plugin_manager = PluginManager()

if __name__ == "__main__":
    # Test plugin discovery
    print("\n" + "="*50)
    print("Plugin Manager Test")
    print("="*50 + "\n")
    
    plugins = plugin_manager.get_all_plugins()
    print(f"Found {len(plugins)} plugins:\n")
    
    for plugin in plugins:
        status_icon = "✓" if plugin['enabled'] else "✗"
        print(f"{status_icon} {plugin['name']} (v{plugin['version']})")
        print(f"  ID: {plugin['id']}")
        print(f"  Description: {plugin['description']}")
        print(f"  Status: {plugin['status']}")
        print()
