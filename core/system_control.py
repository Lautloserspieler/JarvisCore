"""
Systemsteuerungsmodul fuer J.A.R.V.I.S.
Verwaltet Systemoperationen und Programmsteuerung
"""

import os
import sys
import subprocess
import platform
import psutil
import threading
import time
import base64
import ctypes
from ctypes import wintypes
import datetime
import io
import socket
import shutil
import difflib
import re
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests

from core.security_manager import SecurityManager
from utils.logger import Logger


class SystemServiceClient:
    """HTTP-Client fuer den Go-basierten systemd-Service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout: float = 5.0,
        logger: Optional[Logger] = None,
    ) -> None:
        env_disable = os.getenv("JARVIS_SYSTEMD_ENABLED")
        disable_flag = env_disable is not None and env_disable.strip().lower() in {"0", "false", "no"}
        chosen_url = base_url or os.getenv("JARVIS_SYSTEMD_URL") or "http://127.0.0.1:7073"
        if disable_flag:
            chosen_url = ""
        self.base_url = chosen_url.rstrip("/") if chosen_url else ""
        self.token = token or os.getenv("JARVIS_SYSTEMD_TOKEN") or os.getenv("SYSTEMD_TOKEN")
        self.timeout = timeout
        self.enabled = bool(self.base_url)
        self.logger = logger or Logger()
        self.session = requests.Session()

    @classmethod
    def from_env(cls, logger: Optional[Logger] = None, settings: Any = None) -> "SystemServiceClient":
        base_url = None
        token = None
        timeout = 5.0
        try:
            raw_settings = getattr(settings, "settings", {}) if settings else {}
            go_cfg = raw_settings.get("go_services") or {}
            sys_cfg = go_cfg.get("systemd", go_cfg) if isinstance(go_cfg, dict) else {}
            if isinstance(sys_cfg, dict):
                base_url = sys_cfg.get("base_url") or sys_cfg.get("url")
                token = sys_cfg.get("token") or sys_cfg.get("api_key")
                timeout = float(sys_cfg.get("timeout_seconds", timeout))
        except Exception:
            pass
        return cls(base_url=base_url, token=token, timeout=timeout, logger=logger)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        return headers

    def get_resources(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            resp = self.session.get(f"{self.base_url}/system/resources", headers=self._headers(), timeout=self.timeout)
            if resp.ok:
                return resp.json()
        except Exception as exc:
            self.logger.debug("systemd resources fehlgeschlagen: %s", exc)
        return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            resp = self.session.get(f"{self.base_url}/system/status", headers=self._headers(), timeout=self.timeout)
            if resp.ok:
                return resp.json()
        except Exception as exc:
            self.logger.debug("systemd status fehlgeschlagen: %s", exc)
        return None


class SystemControl:
    """Systemsteuerung und Programmverwaltung"""

    def __init__(self, security_manager: Optional[SecurityManager] = None, settings: Any = None):
        self.logger = Logger()
        self.settings = settings
        self.systemd_client = SystemServiceClient.from_env(logger=self.logger)
        if security_manager is None:
            raise ValueError("SystemControl requires an explicit SecurityManager instance.")
        if not isinstance(security_manager, SecurityManager):
            raise TypeError("security_manager must be an instance of SecurityManager.")
        self.security = security_manager
        if not getattr(self.security, "allowed_read_dirs", None) or not getattr(self.security, "allowed_write_dirs", None):
            raise ValueError("Security policy is incomplete: allowed read/write directories must be configured.")
        self.system = platform.system().lower()
        self.running_processes: Dict[str, subprocess.Popen] = {}

        # Programmpfade fuer verschiedene Betriebssysteme
        self.program_paths = self.get_program_paths()
        self.program_close_map = self.get_program_close_map()
        self.dynamic_programs = {}
        self.dynamic_alias_map = {}
        self._normalize_trans = str.maketrans({'\u00e4': 'ae', '\u00f6': 'oe', '\u00fc': 'ue', '\u00df': 'ss', '\u00c4': 'ae', '\u00d6': 'oe', '\u00dc': 'ue'})
        if self.system == 'windows':
            self._index_windows_shortcuts()

        self._safe_mode_active = False
        self._safe_mode_state: Dict[str, Any] = {}
        self._safe_mode_lock = threading.Lock()
        self._safe_mode_dryrun = self._determine_safe_mode_dry_run()
        if not self._safe_mode_dryrun and not getattr(self.security, "write_require_confirmation", True):
            self.logger.warning("Safe-Mode Dry-Run erzwungen: Schreiboperationen erfordern keine Bestaetigung.")
            self._safe_mode_dryrun = True
        self._last_disabled_adapters: List[str] = []
        self._write_protection_backup: Dict[str, Dict[str, int]] = {}

        self.logger.info(f"Systemsteuerung initialisiert fuer {self.system}")

    def _determine_safe_mode_dry_run(self) -> bool:
        """
        Bestimmt, ob Safe-Mode-Aktionen nur simuliert werden sollen.

        Prioritäten:
            1. Umgebungsvariable JARVIS_SAFE_MODE_APPLY (0 => dry-run)
            2. settings.security.safe_mode.apply_changes + explicit_apply (True => real)
            3. Standard: Dry-Run aktiv (True)
        """
        env_value = os.environ.get("JARVIS_SAFE_MODE_APPLY")
        if env_value is not None:
            return env_value.strip() == "0"
        safe_mode_cfg: Dict[str, Any] = {}
        try:
            if self.settings:
                security_cfg = self.settings.get("security", {}) or {}
                safe_mode_cfg = security_cfg.get("safe_mode", {}) or {}
        except Exception as exc:
            self.logger.debug("Safe-Mode-Konfiguration konnte nicht gelesen werden: %s", exc)
            safe_mode_cfg = {}
        if isinstance(safe_mode_cfg, dict):
            apply_changes = bool(safe_mode_cfg.get("apply_changes"))
            explicit_apply = bool(safe_mode_cfg.get("explicit_apply"))
            if apply_changes and explicit_apply:
                return False
            if apply_changes and not explicit_apply:
                self.logger.warning(
                    "Safe-Mode apply angefordert, aber 'explicit_apply' fehlt – bleibe im Dry-Run."
                )
        return True

    def get_program_paths(self):
        """Definiert Programmpfade f?r verschiedene Betriebssysteme"""
        if self.system == "windows":
            return {
                'notepad': 'notepad.exe',
                'calculator': 'calc.exe',
                'cmd': 'cmd.exe',
                'powershell': 'powershell.exe',
                'explorer': 'explorer.exe',
                'browser': 'start chrome',
                'edge': 'start msedge',
                'paint': 'mspaint.exe',
                'word': 'start winword',
                'excel': 'start excel',
                'powerpoint': 'start powerpnt',
                'spotify': 'start spotify',
                'vscode': 'start code'
            }
        elif self.system == "linux":
            return {
                'notepad': ['gedit', 'nano', 'vim'],
                'calculator': ['gnome-calculator', 'kcalc', 'qalculate'],
                'cmd': ['gnome-terminal', 'konsole', 'xterm'],
                'powershell': ['pwsh', 'powershell'],
                'explorer': ['nautilus', 'dolphin', 'thunar'],
                'browser': ['firefox', 'google-chrome', 'chromium'],
                'edge': ['microsoft-edge', 'microsoft-edge-stable'],
                'paint': ['pinta', 'kolourpaint'],
                'word': ['libreoffice --writer', 'lowriter'],
                'excel': ['libreoffice --calc', 'localc'],
                'powerpoint': ['libreoffice --impress', 'loimpress'],
                'spotify': ['spotify'],
                'vscode': ['code', 'code-insiders']
            }
        elif self.system == "darwin":
            return {
                'notepad': 'open -a TextEdit',
                'calculator': 'open -a Calculator',
                'cmd': 'open -a Terminal',
                'powershell': 'open -a Terminal',
                'explorer': 'open .',
                'browser': 'open -a Safari',
                'edge': 'open -a "Microsoft Edge"',
                'paint': 'open -a Preview',
                'word': 'open -a "Microsoft Word"',
                'excel': 'open -a "Microsoft Excel"',
                'powerpoint': 'open -a "Microsoft PowerPoint"',
                'spotify': 'open -a Spotify',
                'vscode': 'open -a "Visual Studio Code"'
            }
        else:
            return {}

    def get_program_close_map(self):
        """Definiert Prozessnamen f?r das Beenden von Programmen"""
        if self.system == "windows":
            return {
                'notepad': ['notepad.exe'],
                'calculator': ['calculator.exe', 'calc.exe'],
                'cmd': ['cmd.exe'],
                'powershell': ['powershell.exe', 'pwsh.exe'],
                'browser': ['chrome.exe', 'firefox.exe', 'msedge.exe'],
                'edge': ['msedge.exe'],
                'paint': ['mspaint.exe'],
                'word': ['winword.exe'],
                'excel': ['excel.exe'],
                'powerpoint': ['powerpnt.exe'],
                'spotify': ['spotify.exe'],
                'vscode': ['code.exe', 'codehelper.exe']
            }
        elif self.system == "linux":
            return {
                'notepad': ['gedit', 'nano', 'vim'],
                'calculator': ['gnome-calculator', 'kcalc', 'qalculate'],
                'cmd': ['gnome-terminal', 'konsole', 'xterm'],
                'powershell': ['pwsh', 'powershell'],
                'browser': ['firefox', 'google-chrome', 'chromium'],
                'edge': ['microsoft-edge', 'microsoft-edge-stable'],
                'paint': ['pinta', 'kolourpaint'],
                'word': ['libreoffice'],
                'excel': ['libreoffice'],
                'powerpoint': ['libreoffice'],
                'spotify': ['spotify'],
                'vscode': ['code', 'code-insiders']
            }
        elif self.system == "darwin":
            return {
                'notepad': ['TextEdit'],
                'calculator': ['Calculator'],
                'cmd': ['Terminal'],
                'powershell': ['Terminal'],
                'browser': ['Safari'],
                'edge': ['Microsoft Edge'],
                'paint': ['Preview'],
                'word': ['Microsoft Word'],
                'excel': ['Microsoft Excel'],
                'powerpoint': ['Microsoft PowerPoint'],
                'spotify': ['Spotify'],
                'vscode': ['Visual Studio Code']
            }
        else:
            return {}
    # ------------------------------------------------------------------
    # Security helpers
    # ------------------------------------------------------------------
    def _ensure_security_manager(self) -> SecurityManager:
        if not self.security:
            raise RuntimeError("Security manager is not configured for system control operations.")
        return self.security

    def _ensure_capability(self, capability: str) -> None:
        manager = self._ensure_security_manager()
        if not manager.can(capability):
            raise PermissionError(f"Capability '{capability}' is disabled by the security policy.")

    def _resolve_read_path(self, raw_path: Union[str, Path]) -> Path:
        manager = self._ensure_security_manager()
        return manager.ensure_path_permission("read", raw_path)

    @staticmethod
    def _format_timestamp(ts: float) -> str:
        return datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")

    @staticmethod
    def _is_hidden(path: Path) -> bool:
        if path.name.startswith('.'):
            return True
        if os.name == 'nt':
            try:
                attribute = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attribute == -1:
                    return False
                return bool(attribute & 0x2)
            except Exception:
                return False
        return False

    def _get_user32(self):
        if self.system != "windows":
            raise NotImplementedError("Window enumeration is only available on Windows systems")
        return ctypes.windll.user32

    def _describe_path(self, path: Path) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "name": path.name,
            "path": str(path),
            "type": "directory" if path.is_dir() else "file",
            "hidden": self._is_hidden(path)
        }
        try:
            stat_result = path.stat()
            info["size"] = stat_result.st_size
            info["created"] = self._format_timestamp(stat_result.st_ctime)
            info["modified"] = self._format_timestamp(stat_result.st_mtime)
            info["accessed"] = self._format_timestamp(stat_result.st_atime)
            info["read_only"] = not os.access(path, os.W_OK)
        except Exception as exc:
            info["error"] = str(exc)
        return info

    # ------------------------------------------------------------------
    # Read-only operations
    # ------------------------------------------------------------------
    def list_directory(self, directory: Union[str, Path], include_hidden: bool = False, max_entries: int = 500) -> Dict[str, Any]:
        base_path = self._resolve_read_path(directory)
        if not base_path.exists():
            raise FileNotFoundError(f"Directory {base_path} does not exist")
        if not base_path.is_dir():
            raise NotADirectoryError(f"{base_path} is not a directory")

        entries: List[Dict[str, Any]] = []
        truncated = False
        for item in sorted(base_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if len(entries) >= max_entries:
                truncated = True
                break
            if not include_hidden and self._is_hidden(item):
                continue
            entries.append(self._describe_path(item))

        self.logger.debug(f"Listed directory {base_path} with {len(entries)} entries")
        return {
            "path": str(base_path),
            "entries": entries,
            "truncated": truncated
        }

    def read_file(self, file_path: Union[str, Path], encoding: str = "utf-8", max_bytes: Optional[int] = None) -> Dict[str, Any]:
        path = self._resolve_read_path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File {path} not found")

        stat_result = path.stat()
        manager = self._ensure_security_manager()
        manager.enforce_file_size_limit(path, stat_result.st_size)

        read_limit = max_bytes or manager.max_read_size_bytes or stat_result.st_size
        read_limit = min(read_limit, stat_result.st_size)
        if read_limit <= 0:
            read_limit = stat_result.st_size

        with path.open('rb') as handle:
            data = handle.read(read_limit)

        truncated = len(data) < stat_result.st_size
        content_type = "text"
        try:
            text_content = data.decode(encoding)
            payload = text_content
        except UnicodeDecodeError:
            content_type = "base64"
            payload = base64.b64encode(data).decode("ascii")
            encoding = "binary"

        return {
            "path": str(path),
            "size": stat_result.st_size,
            "content": payload,
            "content_type": content_type,
            "encoding": encoding,
            "truncated": truncated
        }

    def get_file_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        path = self._resolve_read_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        info = self._describe_path(path)
        info["exists"] = True
        info["path"] = str(path)
        return info

    def get_system_metrics(self) -> Dict[str, Any]:
        self._ensure_capability("system_info")
        try:
            remote = self.systemd_client.get_resources()
            if remote:
                return remote
        except Exception:
            self.logger.debug("systemd get_system_metrics fallback auf lokal", exc_info=True)

        cpu_percent = psutil.cpu_percent(interval=0.2)
        cpu_times = psutil.cpu_times_percent(interval=None, percpu=False)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage(str(Path.home().anchor or Path.home()))
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="seconds")

        gpu_stats: List[Dict[str, Any]] = []
        try:
            import GPUtil  # type: ignore

            for gpu in GPUtil.getGPUs():
                gpu_stats.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "load_percent": round(gpu.load * 100, 2),
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_used_mb": gpu.memoryUsed,
                    "temperature_c": gpu.temperature
                })
        except Exception:
            gpu_stats = []

        return {
            "cpu": {
                "percent": cpu_percent,
                "times_percent": cpu_times._asdict() if hasattr(cpu_times, "_asdict") else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "boot_time": boot_time,
            "gpu": gpu_stats
        }

    def get_network_status(self) -> Dict[str, Any]:
        self._ensure_capability("network_info")
        interfaces = {}
        for name, addrs in psutil.net_if_addrs().items():
            entries = []
            for addr in addrs:
                entries.append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            interfaces[name] = entries

        counters = psutil.net_io_counters(pernic=True)
        interface_stats = {
            name: {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errin": stats.errin,
                "errout": stats.errout,
                "dropin": stats.dropin,
                "dropout": stats.dropout
            }
            for name, stats in counters.items()
        }

        return {
            "hostname": socket.gethostname(),
            "interfaces": interfaces,
            "statistics": interface_stats
        }

    def list_processes(self, limit: int = 50, sort_by: str = "memory") -> List[Dict[str, Any]]:
        self._ensure_capability("process_listing")
        process_info: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(attrs=['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                info = proc.info
                memory_info = info.get('memory_info')
                process_info.append({
                    "pid": info.get('pid'),
                    "name": info.get('name'),
                    "username": info.get('username'),
                    "cpu_percent": info.get('cpu_percent'),
                    "memory_rss": getattr(memory_info, 'rss', None),
                    "create_time": self._format_timestamp(info.get('create_time')) if info.get('create_time') else None
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        reverse = True
        if sort_by == "cpu":
            key_func = lambda item: item.get("cpu_percent") or 0.0
        else:
            key_func = lambda item: item.get("memory_rss") or 0
        sorted_processes = sorted(process_info, key=key_func, reverse=reverse)
        return sorted_processes[:limit]

    def get_event_logs(self, log_name: str = "System", count: int = 25) -> Dict[str, Any]:
        self._ensure_capability("event_logs")
        if self.system != "windows":
            raise NotImplementedError("Windows-Event-Logs sind nur unter Windows verfuegbar.")
        try:
            cmd = [
                "wevtutil",
                "qe",
                log_name,
                f"/c:{count}",
                "/rd:true",
                "/f:text"
            ]
            output = subprocess.check_output(cmd, encoding='utf-8', stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Fehler beim Auslesen des Event-Logs: {exc.output}") from exc
        except FileNotFoundError as exc:
            raise RuntimeError("wevtutil nicht verfuegbar") from exc

        return {
            "log": log_name,
            "entries": output
        }

    def list_windows(self, include_minimized: bool = False) -> List[Dict[str, Any]]:
        self._ensure_capability("window_introspection")
        if self.system != "windows":
            raise NotImplementedError("Fenster-Auflistung wird nur unter Windows unterstuetzt")

        user32 = self._get_user32()
        results: List[Dict[str, Any]] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum_callback(hwnd, _):
            if not include_minimized and not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if not title.strip():
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = None
            try:
                process = psutil.Process(pid.value)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                process_name = None
            results.append({
                "hwnd": hwnd,
                "title": title,
                "process_id": pid.value,
                "process_name": process_name,
                "is_visible": bool(user32.IsWindowVisible(hwnd))
            })
            return True

        user32.EnumWindows(enum_callback, 0)
        return results

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        self._ensure_capability("window_introspection")
        if self.system != "windows":
            raise NotImplementedError("Fensterinformationen sind nur unter Windows verfuegbar")
        user32 = self._get_user32()
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_name = None
        try:
            process = psutil.Process(pid.value)
            process_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            process_name = None
        return {
            "hwnd": hwnd,
            "title": title,
            "process_id": pid.value,
            "process_name": process_name
        }

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def create_directory(self, directory: Union[str, Path], *, exist_ok: bool = True, confirm: bool = False) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        target = manager.ensure_write_permission(directory, confirmed=confirm, check_parent=True, require_exists=False)
        created = False
        if target.exists():
            if not target.is_dir():
                raise FileExistsError(f"{target} exists and is not a directory")
            if not exist_ok:
                raise FileExistsError(f"Directory {target} already exists")
        else:
            target.mkdir(parents=True, exist_ok=True)
            created = True
        return {
            "path": str(target),
            "created": created,
            "info": self._describe_path(target)
        }

    def create_file(
        self,
        file_path: Union[str, Path],
        *,
        content: Union[str, bytes] = "",
        encoding: str = "utf-8",
        overwrite: bool = False,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        target = manager.ensure_write_permission(file_path, confirmed=confirm, check_parent=True, require_exists=False)
        if target.exists() and not overwrite:
            raise FileExistsError(f"File {target} already exists")
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(str(content), encoding=encoding)
        return {
            "path": str(target),
            "size": target.stat().st_size,
            "info": self._describe_path(target)
        }

    def rename_path(self, source: Union[str, Path], destination: Union[str, Path], *, confirm: bool = False) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        src = self._resolve_read_path(source)
        manager.ensure_write_permission(src, confirmed=confirm, require_exists=True)
        dest = manager.ensure_write_permission(destination, confirmed=confirm, check_parent=True, require_exists=False)
        dest.parent.mkdir(parents=True, exist_ok=True)
        result = src.rename(dest)
        return {
            "from": str(src),
            "to": str(result),
            "info": self._describe_path(result)
        }

    def copy_path(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        *,
        overwrite: bool = False,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        src = self._resolve_read_path(source)
        dest = manager.ensure_write_permission(destination, confirmed=confirm, check_parent=True, require_exists=False)
        if dest.exists():
            if not overwrite:
                raise FileExistsError(f"Destination {dest} already exists")
            if dest.is_file():
                dest.unlink()
            else:
                shutil.rmtree(dest)
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        return {
            "from": str(src),
            "to": str(dest),
            "info": self._describe_path(dest)
        }

    def move_path(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        *,
        overwrite: bool = False,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        src = self._resolve_read_path(source)
        manager.ensure_write_permission(src, confirmed=confirm, require_exists=True)
        dest = manager.ensure_write_permission(destination, confirmed=confirm, check_parent=True, require_exists=False)
        if dest.exists():
            if not overwrite:
                raise FileExistsError(f"Destination {dest} already exists")
            if dest.is_file():
                dest.unlink()
            else:
                shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        result = shutil.move(str(src), str(dest))
        return {
            "from": str(src),
            "to": result,
            "info": self._describe_path(Path(result))
        }

    def delete_path(self, target_path: Union[str, Path], *, confirm: bool = False, force: bool = False) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        target = manager.ensure_write_permission(target_path, confirmed=confirm, require_exists=True)
        info = self._describe_path(target)
        if target.is_dir():
            if not force and any(target.iterdir()):
                raise PermissionError(f"Directory {target} is not empty. Use force=True to remove recursively.")
            shutil.rmtree(target)
        else:
            target.unlink()
        return {
            "path": str(target),
            "removed": True,
            "previous": info
        }

    def run_shell_command(
        self,
        command_name: str,
        *,
        confirm: bool = False,
        timeout: int = 120,
        use_shell: bool = False,
    ) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        command = manager.ensure_command_allowed(command_name, confirmed=confirm)
        if os.name == 'nt':
            cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        else:
            if use_shell or isinstance(command, str):
                completed = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            else:
                completed = subprocess.run(
                    command,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
        return {
            "command": command_name,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def execute_script(self, script_identifier: Union[str, Path], *, confirm: bool = False, timeout: int = 300) -> Dict[str, Any]:
        manager = self._ensure_security_manager()
        script_path = manager.ensure_script_allowed(script_identifier, confirmed=confirm)
        if not script_path.exists():
            raise FileNotFoundError(f"Script {script_path} not found")

        if script_path.suffix.lower() == '.ps1' and os.name == 'nt':
            cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(script_path)]
        elif script_path.suffix.lower() in {'.bat', '.cmd'} and os.name == 'nt':
            cmd = [str(script_path)]
        elif script_path.suffix.lower() == '.py':
            cmd = [sys.executable, str(script_path)]
        else:
            cmd = [str(script_path)]

        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "script": str(script_path),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def run_workflow(
        self,
        workflow: Dict[str, Any],
        *,
        confirm: bool = False,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        manager = self._ensure_security_manager()
        steps = workflow.get("steps")
        if not isinstance(steps, list):
            raise ValueError("Workflow must contain a 'steps' list")
        manager.ensure_workflow_allowed(len(steps), confirmed=confirm)

        results: List[Dict[str, Any]] = []
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                raise ValueError(f"Workflow step {index} is invalid")
            action = step.get("action")
            args = step.get("args", {}) or {}
            step_confirm = step.get("confirm", confirm)

            if action == "sleep":
                duration = float(args.get("seconds", 0))
                if dry_run:
                    results.append({"action": action, "status": "skipped", "note": "dry-run"})
                    continue
                time.sleep(max(0.0, duration))
                results.append({"action": action, "status": "ok", "duration": duration})
                continue

            action_map = {
                "list_directory": self.list_directory,
                "read_file": self.read_file,
                "get_file_metadata": self.get_file_metadata,
                "get_system_metrics": self.get_system_metrics,
                "get_network_status": self.get_network_status,
                "list_processes": self.list_processes,
                "get_event_logs": self.get_event_logs,
                "list_windows": self.list_windows,
                "get_active_window": self.get_active_window,
                "capture_screenshot": self.capture_screenshot,
                "create_directory": self.create_directory,
                "create_file": self.create_file,
                "rename_path": self.rename_path,
                "copy_path": self.copy_path,
                "move_path": self.move_path,
                "delete_path": self.delete_path,
                "run_shell_command": self.run_shell_command,
                "execute_script": self.execute_script,
            }

            method = action_map.get(action)
            if not method:
                raise ValueError(f"Workflow step {index} references unsupported action '{action}'")

            if action in {"create_directory", "create_file", "rename_path", "copy_path", "move_path", "delete_path", "run_shell_command", "execute_script"}:
                args = dict(args)
                args.setdefault("confirm", step_confirm)

            if dry_run:
                results.append({"action": action, "status": "skipped", "note": "dry-run"})
                continue

            outcome = method(**args)
            results.append({"action": action, "status": "ok", "result": outcome})

        return results

    def capture_screenshot(self) -> Dict[str, Any]:
        self._ensure_capability("screenshots")
        try:
            from PIL import ImageGrab  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Screenshot-Funktion erfordert Pillow (PIL)") from exc

        image = ImageGrab.grab()
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
        return {
            "format": "PNG",
            "size": image.size,
            "data_base64": encoded
        }
    def _normalise_program_label(self, label: str) -> str:
        cleaned = (label or '').strip().lower()
        cleaned = cleaned.replace('.lnk', '').replace('.url', '').replace('.appref-ms', '').replace('.exe', '')
        for suffix in (' - verknuepfung', ' - shortcut', ' verknuepfung', ' shortcut'):
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        cleaned = re.sub(r'[^a-z0-9]+', ' ', cleaned)
        return ' '.join(cleaned.split())

    def _register_dynamic_program(self, key: str, *, display: str, path: Path, aliases: List[str]):
        if not key or key in self.program_paths:
            return
        if key in self.dynamic_programs:
            return
        alias_set = {self._normalise_program_label(alias) for alias in aliases if alias}
        alias_set.add(key)
        self.dynamic_programs[key] = {
            'path': path,
            'display': display,
            'aliases': sorted(alias_set),
            'type': path.suffix.lower() if path.suffix else 'exe'
        }
        self.dynamic_alias_map[key] = sorted(alias_set)

    def _index_windows_shortcuts(self) -> None:
        try:
            user_start = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
            common_start = Path(os.environ.get('PROGRAMDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
            candidates = [p for p in (user_start, common_start) if p.exists()]
            for base in candidates:
                for entry in base.rglob('*'):
                    if entry.suffix.lower() not in ('.lnk', '.url', '.appref-ms', '.exe'):
                        continue
                    key = self._normalise_program_label(entry.stem)
                    if not key or key in self.dynamic_programs or key in self.program_paths:
                        continue
                    display = entry.stem.replace(' - Verknuepfung', '').replace(' - Shortcut', '').strip()
                    aliases = [display, key, entry.stem]
                    self._register_dynamic_program(key, display=display or entry.stem, path=entry, aliases=aliases)
        except Exception as exc:
            self.logger.warning(f'Dynamic program index failed: {exc}')

    def _match_dynamic_program(self, program_name: str):
        if not program_name:
            return None
        norm = self._normalise_program_label(program_name)
        if norm in self.dynamic_programs:
            return norm, self.dynamic_programs[norm]
        for key, aliases in self.dynamic_alias_map.items():
            if norm in aliases or program_name.lower() in aliases:
                return key, self.dynamic_programs[key]
        candidates = difflib.get_close_matches(norm, list(self.dynamic_programs.keys()), n=1, cutoff=0.78)
        if candidates:
            key = candidates[0]
            return key, self.dynamic_programs[key]
        return None

    def get_dynamic_program_aliases(self) -> Dict[str, List[str]]:
        return {key: info.get('aliases', []) for key, info in self.dynamic_programs.items()}

    def get_dynamic_program_displays(self) -> Dict[str, str]:
        return {key: info.get('display', key) for key, info in self.dynamic_programs.items()}


    def open_program(self, program_name):
        """Oeffnet ein Programm"""
        try:
            if not program_name:
                return False
            lookup_key = self._normalise_program_label(program_name)
            command = self.program_paths.get(lookup_key)
            dynamic_descriptor = None
            if not command and self.system == "windows":
                match = self._match_dynamic_program(program_name)
                if match:
                    lookup_key, dynamic_descriptor = match

            if command is None and dynamic_descriptor is None:
                self.logger.warning(f"Programm nicht definiert: {program_name}")
                return False

            if dynamic_descriptor is not None:
                return self._launch_dynamic_program(lookup_key, dynamic_descriptor)

            program_cmd = command
            if self.system == "linux" and isinstance(program_cmd, list):
                for cmd in program_cmd:
                    if self.is_program_available(cmd):
                        program_cmd = cmd
                        break
                else:
                    self.logger.error(f"Kein verfuegbares Programm fuer {program_name} gefunden")
                    return False

            if self.system == "windows":
                process = subprocess.Popen(
                    program_cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if 'cmd' in program_cmd else 0
                )
            else:
                process = subprocess.Popen(
                    program_cmd.split() if isinstance(program_cmd, str) else [program_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            self.running_processes[lookup_key] = process
            self.logger.info(f"Programm gestartet: {lookup_key} (PID: {process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Oeffnen von {program_name}: {e}")
            return False

    def _launch_dynamic_program(self, program_key: str, descriptor: Dict[str, Any]) -> bool:
        path = descriptor.get('path')
        if not path:
            return False
        try:
            path_str = str(path)
            suffix = descriptor.get('type', '')
            if suffix in ('.lnk', '.url', '.appref-ms', ''):
                os.startfile(path_str)
            elif suffix == '.exe':
                subprocess.Popen(path_str)
            else:
                os.startfile(path_str)
            self.running_processes[program_key] = None
            self.logger.info(f"Programm gestartet (dynamisch): {descriptor.get('display', program_key)}")
            return True
        except Exception as exc:
            self.logger.error(f"Fehler beim Oeffnen von {descriptor.get('display', program_key)}: {exc}")
            return False

    def is_program_available(self, program_name):
            """Pr??ft ob Programm verf??gbar ist"""
            try:
                subprocess.run(
                    ['which', program_name] if self.system != "windows" else ['where', program_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                return True
            except subprocess.CalledProcessError:
                return False

    def _terminate_tracked_process(self, program_name, process):
        if process is None:
            return False
        try:
            if process.poll() is not None:
                self.logger.info(f"Programm bereits beendet: {program_name}")
                return True
            process.terminate()
            try:
                process.wait(timeout=5)
                self.logger.info(f"Programm beendet: {program_name}")
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"Programm zwangsbeendet: {program_name}")
            return True
        except Exception as exc:
            self.logger.warning(f"Fehler beim Schlie?en von {program_name}: {exc}")
            return False

    def _derive_close_targets(self, program_name):
        command = self.program_paths.get(program_name)
        if not command:
            return []
        commands = command if isinstance(command, list) else [command]
        targets = []
        for cmd in commands:
            if not isinstance(cmd, str):
                continue
            tokens = cmd.strip().split()
            if not tokens:
                continue
            if tokens[0].lower() in {"start", "open", "sudo"}:
                tokens = tokens[1:]
            if tokens and tokens[0].lower() in {"-a", "--app"} and len(tokens) > 1:
                candidate = tokens[1]
            elif tokens:
                candidate = tokens[0]
            else:
                continue
            candidate = candidate.strip('"')
            if self.system == "windows" and not candidate.lower().endswith('.exe'):
                candidate = f"{candidate}.exe"
            targets.append(candidate)
        return targets

    def _terminate_by_identifier(self, identifiers):
        if not identifiers:
            return False
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        raw_identifiers = []
        normalized = []
        for ident in identifiers:
            if not ident:
                continue
            clean = ident.strip().strip('"')
            raw_identifiers.append(clean)
            normalized.append(clean.lower())
        if not raw_identifiers:
            return False
        success = False
        for ident in raw_identifiers:
            try:
                if self.system == "windows":
                    result = subprocess.run(
                        ["taskkill", "/IM", ident, "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    if result.returncode == 0:
                        self.logger.info(f"Taskkill ausgef?hrt f?r {ident}")
                        success = True
                else:
                    result = subprocess.run(
                        ["pkill", "-f", ident],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    if result.returncode == 0:
                        self.logger.info(f"pkill ausgef?hrt f?r {ident}")
                        success = True
            except Exception as exc:
                self.logger.debug(f"Konnte Prozessbefehl f?r {ident} nicht ausf?hren: {exc}")
        victims = []
        for proc in psutil.process_iter(['pid', 'name']):
            name = (proc.info.get('name') or '').lower()
            if any(ident in name for ident in normalized):
                victims.append(proc)
        if victims:
            for proc in victims:
                try:
                    proc.terminate()
                    success = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            try:
                gone, alive = psutil.wait_procs(victims, timeout=3)
                for proc in alive:
                    try:
                        proc.kill()
                        success = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                pass
        return success
    def close_program(self, program_name):
        """Schlie?t ein Programm"""
        try:
            if self.system == 'windows':
                program_key = self._normalise_program_label(program_name)
            else:
                program_key = (program_name or '').lower().strip()
            if not program_key:
                return False

            success = False
            if program_key in self.running_processes:
                process = self.running_processes.get(program_key)
                if self._terminate_tracked_process(program_key, process):
                    success = True
                self.running_processes.pop(program_key, None)

            if not success:
                targets = self.program_close_map.get(program_key)
                if not targets:
                    targets = self._derive_close_targets(program_key)
                if targets:
                    success = self._terminate_by_identifier(targets)

            if success:
                return True

            self.logger.warning(f"Konnte {program_key} nicht schlie?en - Prozess nicht gefunden.")
            return False

        except Exception as e:
            self.logger.error(f"Fehler beim Schlie?en von {program_name}: {e}")
            return False

    def get_system_status(self):
        """Ruft aktuellen Systemstatus ab"""
        try:
            status = {
                'cpu': round(psutil.cpu_percent(interval=1), 1),
                'memory': round(psutil.virtual_memory().percent, 1),
                'disk': round(psutil.disk_usage('/').percent, 1) if self.system != "windows" else round(psutil.disk_usage('C:').percent, 1),
                'uptime': self.get_uptime(),
                'processes': len(psutil.pids()),
                'network': self.get_network_status()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Fehler beim Systemstatus: {e}")
            return {
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'uptime': 'Unbekannt',
                'processes': 0,
                'network': 'Unbekannt'
            }
    
    def get_uptime(self):
        """Gibt Systemlaufzeit zur??ck"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception as e:
            self.logger.error(f"Fehler bei Uptime-Berechnung: {e}")
            return "Unbekannt"
    
    def get_running_processes(self):
        """Gibt Liste laufender Prozesse zur??ck"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Nach CPU-Nutzung sortieren
            return sorted(processes, key=lambda x: x['cpu'], reverse=True)[:10]
            
        except Exception as e:
            self.logger.error(f"Fehler bei Prozessliste: {e}")
            return []
    
    def open_file_or_folder(self, path):
        """??ffnet Datei oder Ordner im Standard-Programm"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                self.logger.warning(f"Pfad existiert nicht: {path}")
                return False
            
            if self.system == "windows":
                os.startfile(path)
            elif self.system == "darwin":
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
            
            self.logger.info(f"Ge??ffnet: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim ??ffnen von {path}: {e}")
            return False
    
    def shutdown_system(self, delay_minutes=0):
        """F??hrt System herunter (mit optionaler Verz??gerung)"""
        try:
            self.logger.warning(f"System-Shutdown angefordert (Verz??gerung: {delay_minutes} Min)")
            
            if self.system == "windows":
                cmd = f"shutdown /s /t {delay_minutes * 60}"
            else:
                cmd = f"sudo shutdown -h +{delay_minutes}" if delay_minutes > 0 else "sudo shutdown -h now"
            
            subprocess.run(cmd.split(), check=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim System-Shutdown: {e}")
            return False
    
    def restart_system(self, delay_minutes=0):
        """Startet System neu (mit optionaler VerzÃ¶gerung)"""
        try:
            self.logger.warning(f"System-Restart angefordert (VerzÃ¶gerung: {delay_minutes} Min)")
            if self.system == "windows":
                cmd = f"shutdown /r /t {delay_minutes * 60}"
            else:
                cmd = f"sudo shutdown -r +{delay_minutes}" if delay_minutes > 0 else "sudo shutdown -r now"
            subprocess.run(cmd.split(), check=True)
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim System-Restart: {e}")
            return False

    def lock_workstation(self) -> bool:
        """Sperrt die aktuelle Benutzersitzung (nur Windows)."""
        if self.system != "windows":
            self.logger.warning("Workstation-Lock wird nur unter Windows unterstÃ¼tzt")
            return False
        try:
            ctypes.windll.user32.LockWorkStation()
            self.logger.info("Workstation wurde gesperrt")
            return True
        except Exception as exc:
            self.logger.error(f"LockWorkStation fehlgeschlagen: {exc}")
            return False

    def play_alarm(self, duration_seconds: float = 5.0) -> bool:
        """Spielt einen Alarmton ab."""
        try:
            end_time = time.time() + max(1.0, duration_seconds)
            if self.system == "windows":
                import winsound  # type: ignore
                while time.time() < end_time:
                    winsound.Beep(880, 350)
                    winsound.Beep(660, 250)
            else:
                while time.time() < end_time:
                    print("\a", end='', flush=True)
                    time.sleep(0.4)
            return True
        except Exception as exc:
            self.logger.error(f"Alarmton konnte nicht abgespielt werden: {exc}")
            return False

    # ------------------------------------------------------------------
    # Sicherheitsmodus / SNP-Unterstützung
    # ------------------------------------------------------------------
    def enter_safe_mode(self, *, reasons: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Versetzt das System in einen isolierten Sicherheitsmodus.

        Standardmäßig werden nur Simulationen durchgeführt, um unbeabsichtigte Änderungen
        am Produktivsystem zu vermeiden. Über die Einstellungen oder Umgebungsvariablen
        kann das Verhalten angepasst werden.
        """
        with self._safe_mode_lock:
            if self._safe_mode_active:
                self.logger.info("Safe-Mode bereits aktiv – verwende vorhandenen Status.")
                return {"already_active": True, **self._safe_mode_state}

            reasons = reasons or []
            outcome: Dict[str, Any] = {
                "dry_run": self._safe_mode_dryrun,
                "reasons": reasons,
                "network": False,
                "write_protection": {},
                "processes_terminated": [],
            }

            # Netzwerk deaktivieren
            try:
                if self._safe_mode_dryrun:
                    self.logger.info("Safe-Mode (Simulation): Netzwerk bleibt aktiv.")
                    outcome["network"] = "simulation"
                    outcome["disabled_adapters"] = []
                else:
                    outcome["network"] = self.disconnect_network()
                    outcome["disabled_adapters"] = list(self._last_disabled_adapters)
            except Exception as exc:
                self.logger.error(f"Netzwerk-Isolation fehlgeschlagen: {exc}")
                outcome["network_error"] = str(exc)
                outcome.setdefault("disabled_adapters", [])

            # Schreibschutz auf sensible Pfade anwenden
            try:
                protected_paths = [
                    Path("models"),
                    Path("data/knowledge"),
                    Path("config"),
                ]
                outcome["write_protection"] = self._apply_write_protection(
                    protected_paths,
                    enable=True,
                    simulate=self._safe_mode_dryrun,
                )
            except Exception as exc:
                self.logger.error(f"Schreibschutz konnte nicht gesetzt werden: {exc}")
                outcome["write_protection_error"] = str(exc)

            # Laufende Prozesse bestmöglich terminieren
            terminated = []
            for name, proc in list(self.running_processes.items()):
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        terminated.append(name)
                except Exception:
                    continue
            outcome["processes_terminated"] = terminated

            self._safe_mode_state = outcome
            self._safe_mode_active = True
            self.logger.info("Safe-Mode aktiviert (dry_run=%s)", self._safe_mode_dryrun)
            return outcome

    def exit_safe_mode(self) -> Dict[str, Any]:
        """Hebt den Sicherheitsmodus auf und setzt Simulationen zurück."""
        with self._safe_mode_lock:
            if not self._safe_mode_active:
                return {"active": False}

            outcome: Dict[str, Any] = {"active": False}
            try:
                if self._safe_mode_dryrun:
                    outcome["network"] = "simulation"
                else:
                    outcome["network"] = self._restore_network()
            except Exception as exc:
                outcome["network_error"] = str(exc)

            try:
                protected_paths = [
                    Path("models"),
                    Path("data/knowledge"),
                    Path("config"),
                ]
                self._apply_write_protection(
                    protected_paths,
                    enable=False,
                    simulate=self._safe_mode_dryrun,
                )
            except Exception:
                pass

            self._safe_mode_state = {}
            self._safe_mode_active = False
            self.logger.info("Safe-Mode beendet")
            return outcome

    def get_safe_mode_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Safe-Mode-Status fuer APIs/UI zurueck."""
        with self._safe_mode_lock:
            return {
                "active": self._safe_mode_active,
                "dry_run": self._safe_mode_dryrun,
                "state": dict(self._safe_mode_state),
            }

    def get_hardware_health(self) -> Dict[str, Any]:
        """Gibt grundlegende Hardware-Kennzahlen zurück."""
        result: Dict[str, Any] = {}
        try:
            result["cpu_percent"] = psutil.cpu_percent(interval=0.2)
            memory = psutil.virtual_memory()
            result["memory_percent"] = memory.percent
            # Verwende das Wurzel-Laufwerk des Home-Verzeichnisses statt eines festen Laufwerks
            anchor = Path.home().anchor
            disk_path = str(anchor) if anchor else "/"
            result["disk_percent"] = psutil.disk_usage(disk_path).percent
            temperatures = getattr(psutil, "sensors_temperatures", lambda: {})()
            if temperatures:
                result["temperatures"] = {
                    name: readings[0].current if readings else None
                    for name, readings in temperatures.items()
                }
            result["timestamp"] = datetime.datetime.utcnow().isoformat()
        except Exception as exc:
            self.logger.debug(f"Hardwarediagnose eingeschränkt: {exc}")
        return result

    def _apply_write_protection(self, paths: List[Path], *, enable: bool, simulate: bool) -> Dict[str, Any]:
        """Aktiviert oder deaktiviert den Schreibschutz fuer sensible Pfade."""
        outcome: Dict[str, Any] = {}
        for path in paths:
            abs_path = (Path.cwd() / path).resolve()
            path_key = str(abs_path)
            snapshot: Dict[str, int] = {}
            if not abs_path.exists():
                outcome[str(path)] = "missing"
                if not enable:
                    self._write_protection_backup.pop(path_key, None)
                continue
            if simulate:
                outcome[str(path)] = "simulated"
                self.logger.debug("Safe-Mode Simulation: Schreibschutz fuer %s", abs_path)
                continue
            try:
                if enable:
                    snapshot = self._capture_permissions(abs_path)
                    self._write_protection_backup[path_key] = snapshot
                    self._set_read_only(abs_path)
                    outcome[str(path)] = "applied"
                else:
                    snapshot = self._write_protection_backup.pop(path_key, {})
                    self._clear_read_only(abs_path)
                    if snapshot:
                        self._restore_permissions(snapshot)
                        outcome[str(path)] = "restored"
                    else:
                        outcome[str(path)] = "no_backup"
            except Exception as exc:
                if enable:
                    self._write_protection_backup.pop(path_key, None)
                else:
                    if snapshot and path_key not in self._write_protection_backup:
                        self._write_protection_backup[path_key] = snapshot
                outcome[str(path)] = f"error: {exc}"
        return outcome

    def _capture_permissions(self, root: Path) -> Dict[str, int]:
        """Erfasst Dateiberechtigungen fuer anschliessende Wiederherstellung."""
        snapshot: Dict[str, int] = {}
        for target in self._iter_write_targets(root):
            try:
                mode = stat.S_IMODE(target.stat().st_mode)
            except OSError as exc:
                self.logger.debug("Konnte Berechtigungen fuer %s nicht lesen: %s", target, exc)
                continue
            snapshot[str(target)] = mode
        return snapshot

    def _restore_permissions(self, snapshot: Dict[str, int]) -> None:
        """Stellt zuvor gesicherte Dateiberechtigungen wieder her."""
        for target_str, mode in snapshot.items():
            target_path = Path(target_str)
            if not target_path.exists():
                continue
            try:
                os.chmod(target_path, mode)
            except OSError as exc:
                self.logger.warning("Konnte Berechtigungen fuer %s nicht wiederherstellen: %s", target_path, exc)

    def _set_read_only(self, root: Path) -> None:
        """Setzt Dateien/Ordner auf schreibgeschuetzt."""
        if self.system == "windows":
            cmd = ["cmd", "/c", "attrib", "+R", str(root)]
            if root.is_dir():
                cmd.extend(["/S", "/D"])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            return
        file_mode = 0o400
        dir_mode = 0o500
        for target in self._iter_write_targets(root):
            try:
                if target.is_dir():
                    os.chmod(target, dir_mode)
                else:
                    os.chmod(target, file_mode)
            except OSError as exc:
                raise RuntimeError(f"chmod fehlgeschlagen fuer {target}: {exc}") from exc

    def _clear_read_only(self, root: Path) -> None:
        """Entfernt Schreibschutz-Attribute."""
        if self.system == "windows":
            cmd = ["cmd", "/c", "attrib", "-R", str(root)]
            if root.is_dir():
                cmd.extend(["/S", "/D"])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            return
        # Auf POSIX-Systemen sorgt chmod in _restore_permissions fuer die Freigabe.

    def _iter_write_targets(self, root: Path) -> List[Path]:
        """Liefert alle relevanten Pfade (Ordner + Dateien) unterhalb von root."""
        targets: List[Path] = []
        if root.is_symlink():
            targets.append(root)
            return targets
        targets.append(root)
        if root.is_dir():
            for dirpath, dirnames, filenames in os.walk(root):
                base = Path(dirpath)
                for name in dirnames:
                    targets.append(base / name)
                for name in filenames:
                    targets.append(base / name)
        return targets

    def _restore_network(self) -> bool:
        """Stellt deaktivierte Netzwerkadapter wieder her."""
        adapters = list(self._safe_mode_state.get("disabled_adapters", []) or self._last_disabled_adapters)
        if not adapters:
            self.logger.info("Safe-Mode: Keine Netzwerkadapter zur Reaktivierung vermerkt.")
            return True
        if self.system != "windows":
            self.logger.warning("Netzwerk-Reaktivierung wird nur unter Windows unterstuetzt")
            return False
        restored = True
        for name in adapters:
            cmd = f'netsh interface set interface name="{name}" admin=enabled'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                restored = False
                self.logger.error(f"Adapter {name} konnte nicht reaktiviert werden: {result.stderr.strip() or result.stdout.strip()}")
        self._last_disabled_adapters = []
        self._safe_mode_state["disabled_adapters"] = []
        return restored

    def disconnect_network(self) -> bool:
        """Deaktiviert aktive Netzwerkadapter (best effort)."""
        disabled: List[str] = []
        success = False
        if self.system == "windows":
            try:
                stats = psutil.net_if_stats()
                for name, info in stats.items():
                    if not info.isup:
                        continue
                    cmd = f'netsh interface set interface name="{name}" admin=disabled'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        success = True
                        disabled.append(name)
                    else:
                        self.logger.debug(f"Netzwerk {name} konnte nicht deaktiviert werden: {result.stderr.strip()}")
            except Exception as exc:
                self.logger.error(f"Netzwerk konnte nicht deaktiviert werden: {exc}")
                success = False
        else:
            self.logger.warning("Netzwerk-Trennung wird auf diesem System nicht unterstuetzt")
        self._last_disabled_adapters = disabled
        return success

    def trigger_emergency(self, actions: Optional[List[str]] = None) -> Dict[str, bool]:
        """FÃ¼hrt eine Reihe definierter Notfallaktionen aus."""
        actions = actions or ['lock', 'alarm']
        outcomes: Dict[str, bool] = {}
        for action in actions:
            if action == 'lock':
                outcomes['lock'] = self.lock_workstation()
            elif action == 'alarm':
                outcomes['alarm'] = self.play_alarm()
            elif action == 'disconnect':
                outcomes['disconnect'] = self.disconnect_network()
            elif action == 'camera':
                outcomes['camera'] = False
                self.logger.warning('Kamera-Aktivierung ist nicht implementiert')
            else:
                outcomes[action] = False
        return outcomes















