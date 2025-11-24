"""Simple plugin manager to coordinate conversation plugins."""

from __future__ import annotations

import importlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.logger import Logger


class PluginManager:
    """Loads and orchestrates conversation plugins."""

    DEFAULT_REGISTRY: List[Dict[str, Any]] = [
        {
            "name": "memory",
            "module": "plugins.memory_plugin",
            "class": "MemoryPlugin",
            "sandbox": False,
            "enabled": True,
            "timeout": 5.0,
        },
        {
            "name": "clarification",
            "module": "plugins.clarification_plugin",
            "class": "ClarificationPlugin",
            "sandbox": True,
            "enabled": True,
            "timeout": 3.0,
        },
    ]

    def __init__(self, logger: Optional[Logger] = None, registry_path: Optional[Path] = None) -> None:
        self.logger = logger or Logger()
        self.registry_path = Path(registry_path or "config/plugins.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.plugins: List[PluginWrapper] = []
        self.plugin_descriptors: List[Dict[str, Any]] = []
        self.hot_reload_enabled: bool = True
        self._plugin_meta: Dict[str, Dict[str, Any]] = {}
        self._ensure_registry_file()
        self.reload_plugins()

    def _ensure_registry_file(self) -> None:
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps(self.DEFAULT_REGISTRY, indent=2), encoding="utf-8")

    def _load_registry(self) -> List[Dict[str, Any]]:
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Plugin-Registry muss eine Liste sein")
            return data
        except Exception as exc:
            self.logger.error(f"Konnte Plugin-Registry nicht lesen: {exc}")
            return list(self.DEFAULT_REGISTRY)

    def _write_registry(self, registry: List[Dict[str, Any]]) -> None:
        self.registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    def _load_plugins(self) -> List['PluginWrapper']:
        loaded: List[PluginWrapper] = []
        registry = self._load_registry()
        self.plugin_descriptors = registry
        self._plugin_meta = {}
        for descriptor in registry:
            if not descriptor.get("enabled", True):
                continue
            plugin_name = descriptor.get("name") or descriptor.get("class")
            try:
                module = importlib.import_module(descriptor["module"])
                wrapper, factory = self._instantiate_plugin(descriptor, module, plugin_name)
                if not wrapper:
                    continue
                self._register_plugin_metadata(wrapper, descriptor, module, factory)
                loaded.append(wrapper)
                self.logger.info(f"Plugin geladen: {plugin_name}")
            except Exception as exc:
                self.logger.error(f"Plugin konnte nicht geladen werden ({plugin_name}): {exc}")
        return loaded

    def _instantiate_plugin(
        self,
        descriptor: Dict[str, Any],
        module: Any,
        plugin_name: str,
    ) -> Tuple[Optional['PluginWrapper'], Optional[Callable[[], Any]]]:
        plugin_class = getattr(module, descriptor["class"])
        timeout = float(descriptor.get("timeout", 5.0) or 5.0)

        def factory(plugin_class: Any = plugin_class) -> Any:
            return plugin_class(logger=self.logger)

        try:
            if descriptor.get("sandbox"):
                wrapper = ThreadedPluginSandbox(
                    factory,
                    timeout=timeout,
                    logger=self.logger,
                    plugin_name=plugin_name,
                )
            else:
                instance = factory()
                wrapper = PluginWrapper(instance)
        except Exception as exc:
            self.logger.error(f"Plugin {plugin_name} konnte nicht instanziiert werden: {exc}")
            return None, None

        wrapper.plugin_name = plugin_name or getattr(wrapper, "plugin_name", plugin_name)
        return wrapper, factory

    def _register_plugin_metadata(
        self,
        wrapper: 'PluginWrapper',
        descriptor: Dict[str, Any],
        module: Any,
        factory: Optional[Callable[[], Any]],
    ) -> None:
        module_path = getattr(module, "__file__", None)
        mtime = None
        if module_path:
            try:
                mtime = Path(module_path).resolve().stat().st_mtime
            except Exception:
                mtime = None
        self._plugin_meta[wrapper.plugin_name] = {
            "descriptor": dict(descriptor),
            "module": module,
            "module_path": module_path,
            "mtime": mtime,
            "factory": factory,
            "wrapper": wrapper,
        }

    def _maybe_reload_plugin(self, wrapper: 'PluginWrapper') -> 'PluginWrapper':
        if not self.hot_reload_enabled:
            return wrapper
        meta = self._plugin_meta.get(wrapper.plugin_name)
        if not meta:
            return wrapper
        module_path = meta.get("module_path")
        if not module_path:
            return wrapper
        try:
            current_mtime = Path(module_path).resolve().stat().st_mtime
        except FileNotFoundError:
            return wrapper
        except Exception as exc:
            self.logger.debug(f"Hot-Reload Pruefung fehlgeschlagen ({wrapper.plugin_name}): {exc}")
            return wrapper
        previous_mtime = meta.get("mtime")
        if previous_mtime and current_mtime <= previous_mtime:
            return wrapper
        new_wrapper = self._reload_plugin(wrapper.plugin_name, current_mtime)
        return new_wrapper or wrapper

    def _reload_plugin(self, plugin_name: str, current_mtime: float) -> Optional['PluginWrapper']:
        meta = self._plugin_meta.get(plugin_name)
        if not meta:
            return None
        descriptor = meta.get("descriptor") or {}
        module_obj = meta.get("module")
        if module_obj is None:
            return None
        try:
            module = importlib.reload(module_obj)
        except Exception as exc:
            self.logger.error(f"Hot-Reload fuer Plugin {plugin_name} fehlgeschlagen: {exc}")
            meta["mtime"] = current_mtime
            return None
        wrapper, factory = self._instantiate_plugin(descriptor, module, plugin_name)
        if not wrapper:
            meta["mtime"] = current_mtime
            return None
        self._replace_plugin(meta.get("wrapper"), wrapper)
        meta.update(
            {
                "module": module,
                "module_path": getattr(module, "__file__", None),
                "mtime": current_mtime,
                "factory": factory,
                "wrapper": wrapper,
            }
        )
        self.logger.info(f"Plugin hot reloaded: {plugin_name}")
        return wrapper

    def _replace_plugin(self, old_wrapper: Optional['PluginWrapper'], new_wrapper: 'PluginWrapper') -> None:
        if old_wrapper is not None:
            for index, existing in enumerate(self.plugins):
                if existing is old_wrapper:
                    self.plugins[index] = new_wrapper
                    break
            try:
                old_wrapper.shutdown()
            except Exception as exc:
                self.logger.error(f"Plugin-Shutdown fehlgeschlagen ({old_wrapper.plugin_name}): {exc}")
        else:
            self.plugins.append(new_wrapper)

    def reload_plugins(self) -> None:
        self.shutdown()
        self.plugins = self._load_plugins()

    def register_plugin(
        self,
        module: str,
        cls_name: str,
        name: Optional[str] = None,
        sandbox: bool = False,
        enabled: bool = True,
        timeout: float = 5.0,
    ) -> None:
        registry = self._load_registry()
        registry.append(
            {
                "name": name or cls_name,
                "module": module,
                "class": cls_name,
                "sandbox": sandbox,
                "enabled": enabled,
                "timeout": timeout,
            }
        )
        self._write_registry(registry)
        self.reload_plugins()

    def set_plugin_enabled(self, name: str, enabled: bool) -> bool:
        registry = self._load_registry()
        updated = False
        for descriptor in registry:
            if descriptor.get("name") == name or descriptor.get("class") == name:
                descriptor["enabled"] = bool(enabled)
                updated = True
                break
        if updated:
            self._write_registry(registry)
            self.reload_plugins()
            return True
        self.logger.warning(f"Plugin {name} nicht gefunden")
        return False

    def get_plugin_overview(self) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        active_map = {wrapper.plugin_name: wrapper for wrapper in self.plugins}
        overview: List[Dict[str, Any]] = []
        for descriptor in registry:
            plugin_name = descriptor.get("name") or descriptor.get("class") or "unbekannt"
            wrapper = active_map.get(plugin_name)
            if not wrapper:
                wrapper = active_map.get(descriptor.get("class", ""))
            meta = self._plugin_meta.get(wrapper.plugin_name) if wrapper else None
            entry = {
                "name": plugin_name,
                "class": descriptor.get("class"),
                "module": descriptor.get("module"),
                "sandbox": bool(descriptor.get("sandbox", False)),
                "timeout": float(descriptor.get("timeout", 5.0) or 5.0),
                "enabled": bool(descriptor.get("enabled", True)),
                "active": bool(wrapper),
            }
            if meta:
                entry["module_path"] = meta.get("module_path")
                entry["last_reload_epoch"] = meta.get("mtime")
            overview.append(entry)
        return overview

    def get_plugin(self, name: str) -> Optional['PluginWrapper']:
        for wrapper in self.plugins:
            if wrapper.plugin_name == name:
                return wrapper
        for wrapper in self.plugins:
            plugin_obj = getattr(wrapper, "_plugin", None)
            if plugin_obj and plugin_obj.__class__.__name__ == name:
                return wrapper
        return None

    def reload_plugin(self, name: str) -> bool:
        target_key = None
        target_meta: Optional[Dict[str, Any]] = None
        for key, meta in self._plugin_meta.items():
            descriptor = meta.get("descriptor") or {}
            if key == name or descriptor.get("name") == name or descriptor.get("class") == name:
                target_key = key
                target_meta = meta
                break
        if not target_key:
            self.logger.warning(f"Plugin {name} konnte nicht zum Reload gefunden werden")
            return False
        current_mtime = (target_meta or {}).get("mtime")
        result = self._reload_plugin(target_key, current_mtime or time.time())
        return bool(result)

    def handle_user_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        response: Optional[str] = None
        for index, wrapper in enumerate(list(self.plugins)):
            active_wrapper = self._maybe_reload_plugin(wrapper)
            if active_wrapper is not wrapper:
                self.plugins[index] = active_wrapper
                wrapper = active_wrapper
            try:
                plugin_result = wrapper.on_user_message(message, context)
                if response is None and plugin_result:
                    response = plugin_result
            except Exception as exc:
                self.logger.error(f"Plugin-Fehler bei on_user_message ({wrapper.plugin_name}): {exc}")
        return response

    def handle_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        for index, wrapper in enumerate(list(self.plugins)):
            active_wrapper = self._maybe_reload_plugin(wrapper)
            if active_wrapper is not wrapper:
                self.plugins[index] = active_wrapper
                wrapper = active_wrapper
            try:
                wrapper.on_assistant_message(message, context)
            except Exception as exc:
                self.logger.error(f"Plugin-Fehler bei on_assistant_message ({wrapper.plugin_name}): {exc}")

    def get_context_snapshot(self) -> Dict[str, Any]:
        combined: Dict[str, Any] = {}
        for index, wrapper in enumerate(list(self.plugins)):
            active_wrapper = self._maybe_reload_plugin(wrapper)
            if active_wrapper is not wrapper:
                self.plugins[index] = active_wrapper
                wrapper = active_wrapper
            try:
                plugin_context = wrapper.get_context()
                if plugin_context:
                    combined[wrapper.plugin_name] = plugin_context
            except Exception as exc:
                self.logger.error(f"Plugin-Fehler bei get_context ({wrapper.plugin_name}): {exc}")
        return combined

    def shutdown(self) -> None:
        for wrapper in list(self.plugins):
            try:
                wrapper.shutdown()
            except Exception as exc:
                self.logger.error(f"Plugin-Fehler bei shutdown ({wrapper.plugin_name}): {exc}")
        self.plugins = []
        self._plugin_meta = {}


class PluginWrapper:
    """Thin wrapper around a plugin instance."""

    def __init__(self, plugin: Any) -> None:
        self._plugin = plugin
        self.plugin_name = getattr(plugin, "plugin_name", plugin.__class__.__name__)

    def on_user_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        return getattr(self._plugin, "on_user_message", lambda *_: None)(message, context)

    def on_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        handler = getattr(self._plugin, "on_assistant_message", None)
        if handler:
            handler(message, context)

    def get_context(self) -> Dict[str, Any]:
        getter = getattr(self._plugin, "get_context", None)
        return getter() if getter else {}

    def shutdown(self) -> None:
        shutdown_fn = getattr(self._plugin, "shutdown", None)
        if shutdown_fn:
            shutdown_fn()



class ThreadedPluginSandbox(PluginWrapper):
    """Executes plugin hooks in a dedicated thread pool with timeout and auto-reset."""

    def __init__(
        self,
        factory: Callable[[], Any],
        *,
        timeout: float,
        logger: Logger,
        plugin_name: Optional[str] = None,
    ) -> None:
        initial = factory()
        super().__init__(initial)
        self.logger = logger
        self.timeout = timeout
        self._factory = factory
        self.plugin_name = plugin_name or getattr(initial, "plugin_name", initial.__class__.__name__)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"plugin-{self.plugin_name}")
        self._restart_lock = threading.Lock()

    def _ensure_plugin(self) -> bool:
        if self._plugin is None:
            with self._restart_lock:
                if self._plugin is None:
                    try:
                        self._plugin = self._factory()
                    except Exception as exc:
                        self.logger.error(f"Plugin-Neuinitialisierung fehlgeschlagen ({self.plugin_name}): {exc}")
                        return False
        return self._plugin is not None

    def _reset_instance(self) -> None:
        with self._restart_lock:
            current = getattr(self, "_plugin", None)
            self._plugin = None
            if current:
                shutdown_fn = getattr(current, "shutdown", None)
                if shutdown_fn:
                    try:
                        shutdown_fn()
                    except Exception as exc:
                        self.logger.debug(f"Plugin konnte nicht sauber herunterfahren ({self.plugin_name}): {exc}")

    def update_factory(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._reset_instance()

    def _run(self, method_name: str, *args) -> Optional[Any]:
        if not self._ensure_plugin():
            return None
        method = getattr(self._plugin, method_name, None)
        if not method:
            return None
        future = self._executor.submit(method, *args)
        try:
            return future.result(timeout=self.timeout)
        except TimeoutError:
            self.logger.error(f"Plugin-Zeitueberschreitung ({self.plugin_name}) bei {method_name}")
            self._reset_instance()
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"Plugin-Fehler ({self.plugin_name}) bei {method_name}: {exc}")
            self._reset_instance()
        return None

    def on_user_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        return self._run("on_user_message", message, context)

    def on_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        self._run("on_assistant_message", message, context)

    def get_context(self) -> Dict[str, Any]:
        result = self._run("get_context")
        return result or {}

    def shutdown(self) -> None:
        self._reset_instance()
        self._executor.shutdown(wait=False)

