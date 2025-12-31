"""Plugin System Framework for JarvisCore

Extensible plugin architecture with built-in plugins:
- Code Analyzer: AI-powered code review
- Web Search: Search integration
- File Manager: File operations
- Calculator: Mathematical computations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import asyncio
from pathlib import Path
from datetime import datetime
import requests


class PluginInterface(ABC):
    """Base class for all JARVIS plugins"""
    
    def __init__(self):
        self.name: str = "Unknown"
        self.version: str = "1.0.0"
        self.description: str = ""
        self.author: str = "JARVIS Team"
        self.enabled: bool = False
        self.config: Dict[str, Any] = {}
        self.dependencies: List[str] = []
    
    @abstractmethod
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute plugin command
        
        Args:
            command: Command to execute
            **kwargs: Command-specific arguments
            
        Returns:
            Dict with 'success', 'result', and optional 'error'
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return plugin schema (commands, parameters, etc.)"""
        pass
    
    async def on_load(self):
        """Called when plugin is loaded"""
        print(f"[PLUGIN] {self.name} v{self.version} loaded")
    
    async def on_unload(self):
        """Called when plugin is unloaded"""
        print(f"[PLUGIN] {self.name} unloaded")
    
    def validate_dependencies(self) -> bool:
        """Check if all dependencies are satisfied"""
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                print(f"[PLUGIN] {self.name}: Missing dependency {dep}")
                return False
        return True


class CodeAnalyzerPlugin(PluginInterface):
    """Plugin for AI-powered code analysis and review"""
    
    def __init__(self):
        super().__init__()
        self.name = "Code Analyzer"
        self.version = "1.0.0"
        self.description = "Analyze and review code with AI assistance"
        self.author = "JARVIS Team"
    
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute code analysis commands"""
        
        if command == "analyze":
            code = kwargs.get("code", "")
            language = kwargs.get("language", "python")
            
            if not code:
                return {"success": False, "error": "No code provided"}
            
            # Generate AI review
            from core.llama_inference import llama_runtime
            
            if not llama_runtime.is_loaded:
                return {"success": False, "error": "No model loaded"}
            
            result = llama_runtime.generate(
                prompt=f"""Analysiere den folgenden {language} Code und gebe konstruktives Feedback:

```{language}
{code}
```

Fokus:
1. Code Quality & Style
2. Performance Issues
3. Security Concerns
4. Best Practices

Antworte strukturiert und präzise.""",
                max_tokens=1024,
                temperature=0.3  # Lower for more focused analysis
            )
            
            if result['success']:
                return {
                    "success": True,
                    "result": {
                        "analysis": result['text'],
                        "language": language,
                        "lines": len(code.split('\n')),
                        "chars": len(code)
                    }
                }
            else:
                return {"success": False, "error": result.get('error', 'Unknown error')}
        
        elif command == "suggest_refactor":
            code = kwargs.get("code", "")
            
            from core.llama_inference import llama_runtime
            
            if not llama_runtime.is_loaded:
                return {"success": False, "error": "No model loaded"}
            
            result = llama_runtime.generate(
                prompt=f"""Schlage Refactoring-Improvements für diesen Code vor:

```python
{code}
```

Gib konkrete Verbesserungsvorschläge mit Beispielen.""",
                max_tokens=1024
            )
            
            if result['success']:
                return {
                    "success": True,
                    "result": {"suggestions": result['text']}
                }
            else:
                return {"success": False, "error": result.get('error')}
        
        elif command == "find_bugs":
            code = kwargs.get("code", "")
            
            from core.llama_inference import llama_runtime
            
            if not llama_runtime.is_loaded:
                return {"success": False, "error": "No model loaded"}
            
            result = llama_runtime.generate(
                prompt=f"""Finde potenzielle Bugs in diesem Code:

```python
{code}
```

Liste alle gefundenen Probleme auf.""",
                max_tokens=512
            )
            
            if result['success']:
                return {
                    "success": True,
                    "result": {"bugs": result['text']}
                }
            else:
                return {"success": False, "error": result.get('error')}
        
        return {"success": False, "error": f"Unknown command: {command}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "commands": [
                {
                    "name": "analyze",
                    "description": "Analyze code quality and style",
                    "parameters": {
                        "code": {"type": "str", "required": True},
                        "language": {"type": "str", "default": "python"}
                    }
                },
                {
                    "name": "suggest_refactor",
                    "description": "Suggest refactoring improvements",
                    "parameters": {
                        "code": {"type": "str", "required": True}
                    }
                },
                {
                    "name": "find_bugs",
                    "description": "Find potential bugs",
                    "parameters": {
                        "code": {"type": "str", "required": True}
                    }
                }
            ]
        }


class WebSearchPlugin(PluginInterface):
    """Plugin for web search integration via DuckDuckGo"""
    
    def __init__(self):
        super().__init__()
        self.name = "Web Search"
        self.version = "1.0.0"
        self.description = "Search the web and integrate results"
        self.author = "JARVIS Team"
        self.config = {
            "search_engine": "google",
            "max_results": 5
        }
    
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute web search commands"""
        
        if command == "search":
            query = kwargs.get("query", "")
            
            if not query:
                return {"success": False, "error": "No query provided"}
            try:
                response = requests.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    },
                    timeout=10
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                return {"success": False, "error": f"Websuche fehlgeschlagen: {exc}"}

            results: List[Dict[str, str]] = []
            abstract = payload.get("AbstractText")
            abstract_source = payload.get("AbstractSource")
            abstract_url = payload.get("AbstractURL")
            if abstract:
                results.append({
                    "title": payload.get("Heading") or query,
                    "summary": abstract,
                    "source": abstract_source or "DuckDuckGo",
                    "url": abstract_url or ""
                })

            for topic in payload.get("RelatedTopics", []):
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "summary": topic.get("Text", ""),
                        "source": "DuckDuckGo",
                        "url": topic.get("FirstURL", "")
                    })
                elif isinstance(topic, dict) and "Topics" in topic:
                    for subtopic in topic.get("Topics", []):
                        if "Text" in subtopic:
                            results.append({
                                "title": subtopic.get("Text", "").split(" - ")[0],
                                "summary": subtopic.get("Text", ""),
                                "source": "DuckDuckGo",
                                "url": subtopic.get("FirstURL", "")
                            })

            results = results[: self.config.get("max_results", 5)]
            if not results:
                return {"success": False, "error": "Keine Suchergebnisse gefunden"}

            return {
                "success": True,
                "result": {
                    "query": query,
                    "results": results,
                    "source": "DuckDuckGo Instant Answer API"
                }
            }
        
        return {"success": False, "error": f"Unknown command: {command}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "commands": [
                {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {
                        "query": {"type": "str", "required": True}
                    }
                }
            ]
        }


class FileManagerPlugin(PluginInterface):
    """Plugin for file operations"""
    
    def __init__(self):
        super().__init__()
        self.name = "File Manager"
        self.version = "1.0.0"
        self.description = "Read, write, and manage files"
        self.author = "JARVIS Team"
    
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute file operations"""
        
        if command == "read":
            filepath = kwargs.get("filepath", "")
            
            if not filepath:
                return {"success": False, "error": "No filepath provided"}
            
            try:
                path = Path(filepath)
                if not path.exists():
                    return {"success": False, "error": "File not found"}
                
                content = path.read_text(encoding='utf-8')
                return {
                    "success": True,
                    "result": {
                        "content": content,
                        "size": path.stat().st_size,
                        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    }
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif command == "write":
            filepath = kwargs.get("filepath", "")
            content = kwargs.get("content", "")
            
            if not filepath:
                return {"success": False, "error": "No filepath provided"}
            
            try:
                path = Path(filepath)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
                return {
                    "success": True,
                    "result": {"message": f"File written: {filepath}"}
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif command == "list":
            directory = kwargs.get("directory", ".")
            
            try:
                path = Path(directory)
                if not path.is_dir():
                    return {"success": False, "error": "Not a directory"}
                
                files = []
                for item in path.iterdir():
                    files.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0
                    })
                
                return {
                    "success": True,
                    "result": {"files": files, "count": len(files)}
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Unknown command: {command}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "commands": [
                {
                    "name": "read",
                    "description": "Read file contents",
                    "parameters": {
                        "filepath": {"type": "str", "required": True}
                    }
                },
                {
                    "name": "write",
                    "description": "Write content to file",
                    "parameters": {
                        "filepath": {"type": "str", "required": True},
                        "content": {"type": "str", "required": True}
                    }
                },
                {
                    "name": "list",
                    "description": "List directory contents",
                    "parameters": {
                        "directory": {"type": "str", "default": "."}
                    }
                }
            ]
        }


class CalculatorPlugin(PluginInterface):
    """Plugin for mathematical calculations"""
    
    def __init__(self):
        super().__init__()
        self.name = "Calculator"
        self.version = "1.0.0"
        self.description = "Perform mathematical calculations"
        self.author = "JARVIS Team"
    
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute calculator commands"""
        
        if command == "calculate":
            expression = kwargs.get("expression", "")
            
            if not expression:
                return {"success": False, "error": "No expression provided"}
            
            try:
                # Safe eval (only math operations)
                import math
                allowed_names = {
                    "abs": abs, "round": round,
                    "pow": pow, "sqrt": math.sqrt,
                    "sin": math.sin, "cos": math.cos, "tan": math.tan,
                    "pi": math.pi, "e": math.e
                }
                
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                
                return {
                    "success": True,
                    "result": {
                        "expression": expression,
                        "result": result
                    }
                }
            except Exception as e:
                return {"success": False, "error": f"Calculation error: {str(e)}"}
        
        return {"success": False, "error": f"Unknown command: {command}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "commands": [
                {
                    "name": "calculate",
                    "description": "Calculate mathematical expression",
                    "parameters": {
                        "expression": {"type": "str", "required": True}
                    }
                }
            ]
        }


class PluginManager:
    """Manage plugin lifecycle and execution"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_dir = Path("plugins")
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Register built-in plugins
        self._register_builtin_plugins()
    
    def _register_builtin_plugins(self):
        """Register built-in plugins"""
        self.register_plugin(CodeAnalyzerPlugin())
        self.register_plugin(WebSearchPlugin())
        self.register_plugin(FileManagerPlugin())
        self.register_plugin(CalculatorPlugin())
        
        print(f"[INFO] Registered {len(self.plugins)} built-in plugins")
    
    def register_plugin(self, plugin: PluginInterface):
        """Register a plugin"""
        if not plugin.validate_dependencies():
            print(f"[WARNING] Plugin {plugin.name} has missing dependencies")
            return False
        
        self.plugins[plugin.name] = plugin
        return True
    
    async def load_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Load and enable a plugin"""
        if plugin_name not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_name} not found"}
        
        plugin = self.plugins[plugin_name]
        plugin.enabled = True
        await plugin.on_load()
        
        return {"success": True, "message": f"Plugin {plugin_name} loaded"}
    
    async def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Unload and disable a plugin"""
        if plugin_name not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_name} not found"}
        
        plugin = self.plugins[plugin_name]
        plugin.enabled = False
        await plugin.on_unload()
        
        return {"success": True, "message": f"Plugin {plugin_name} unloaded"}
    
    async def execute_plugin(
        self,
        plugin_name: str,
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a plugin command"""
        if plugin_name not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_name} not found"}
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.enabled:
            return {"success": False, "error": f"Plugin {plugin_name} not enabled"}
        
        return await plugin.execute(command, **kwargs)
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get all plugins with their schemas"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled,
                "schema": p.get_schema()
            }
            for p in self.plugins.values()
        ]
    
    def get_plugin(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get specific plugin info"""
        if plugin_name not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_name]
        return {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "author": plugin.author,
            "enabled": plugin.enabled,
            "schema": plugin.get_schema()
        }


# Global instance
plugin_manager = PluginManager()
