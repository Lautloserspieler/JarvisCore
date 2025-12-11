import json
from typing import Dict, List, Any
from pathlib import Path

class PluginManager:
    """Manager for JARVIS plugins"""
    
    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.config_path = self.plugins_dir / "plugins_config.json"
        self.load_config()
    
    def load_config(self):
        """Load plugins configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration - only real plugins
            self.config = {
                'installed_plugins': [
                    {
                        'id': 'wikipedia-search',
                        'name': 'Wikipedia Suche',
                        'description': 'Durchsucht Wikipedia nach Informationen',
                        'version': '1.0.0',
                        'author': 'JARVIS Core Team',
                        'isEnabled': False,
                        'isInstalled': True,
                        'category': 'Wissen',
                        'capabilities': ['search', 'knowledge-base']
                    },
                    {
                        'id': 'web-search',
                        'name': 'Web-Suche',
                        'description': 'Durchsucht das Internet nach aktuellen Informationen',
                        'version': '1.0.0',
                        'author': 'JARVIS Core Team',
                        'isEnabled': False,
                        'isInstalled': True,
                        'category': 'Wissen',
                        'capabilities': ['search', 'web-access']
                    },
                    {
                        'id': 'code-executor',
                        'name': 'Code Executor',
                        'description': 'Führt Python-Code sicher aus',
                        'version': '1.0.0',
                        'author': 'JARVIS Core Team',
                        'isEnabled': False,
                        'isInstalled': True,
                        'category': 'Entwicklung',
                        'capabilities': ['code-execution', 'python']
                    }
                ]
            }
            self.save_config()
    
    def save_config(self):
        """Save plugins configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get all plugins"""
        return self.config['installed_plugins']
    
    def toggle_plugin(self, plugin_id: str) -> bool:
        """Enable/disable a plugin"""
        for plugin in self.config['installed_plugins']:
            if plugin['id'] == plugin_id:
                plugin['isEnabled'] = not plugin['isEnabled']
                self.save_config()
                return True
        return False

# Global instance
plugin_manager = PluginManager()
