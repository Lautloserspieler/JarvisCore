"""Media routing utilities for Jarvis."""

from __future__ import annotations

import time
from typing import Optional, Dict, Any

import shutil
import psutil

try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32process  # type: ignore
except Exception:  # pragma: no cover - optional on non-Windows
    win32api = None
    win32con = None
    win32gui = None
    win32process = None

from utils.logger import Logger
from core.youtube_automator import YouTubeAutomator


class MediaRouter:
    """Dispatches media actions to the appropriate backend (currently YouTube)."""

    def __init__(self, system_control: Optional[object] = None, settings: Optional[object] = None) -> None:
        self.logger = Logger()
        self.system_control = system_control
        self.settings = settings
        self.youtube = YouTubeAutomator(settings=settings)
        self._last_state: Dict[str, Optional[str]] = {
            "target": None,
            "track": None,
            "url": None,
        }
        self._state: Dict[str, Any] = {
            "youtube_active": False,
            "edge_running": False,
            "youtube_window": False,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def play(self, track: str, *, target: Optional[str] = None) -> Dict[str, Any]:
        """Play a track on the selected target."""
        target_key = self._normalize_target(target)
        if target_key != "youtube":
            self.logger.warning(f"Unbekanntes Medienziel '{target_key}' - verwende YouTube.")
            target_key = "youtube"

        if not track:
            return {
                "success": False,
                "target": target_key,
                "url": None,
                "exact": False,
                "message": "Es wurde kein Titel angegeben.",
            }

        success, url, exact = self.youtube.play_track(track)
        if success:
            self._update_state(target_key, track, url, youtube_active=True)
        else:
            # Öffne zumindest die Suchseite, wenn der Automatisierer sie bereitgestellt hat
            self._update_state(target_key, track if exact else "", url, youtube_active=False)
        if success and exact:
            message = f"Starte YouTube-Wiedergabe für '{track}'."
        elif success:
            message = f"Ich öffne die YouTube-Suche nach '{track}'."
        else:
            message = "YouTube konnte nicht gestartet werden."

        self.logger.info(
            "[MediaRouter] action=play target=%s track=%s success=%s exact=%s url=%s",
            target_key,
            track,
            success,
            exact,
            url,
        )

        return {
            "success": success,
            "target": target_key,
            "url": url,
            "exact": exact,
            "message": message,
            "track": track,
        }

    def pause(self) -> bool:
        """Toggle play/pause via global media key."""
        if not self._prepare_for_control("pause"):
            return False
        result = self._send_media_key(self._vk("VK_MEDIA_PLAY_PAUSE"))
        self.logger.info("[MediaRouter] action=pause result=%s", result)
        return result

    def resume(self) -> bool:
        """Alias for pause (media key toggles)."""
        if not self._prepare_for_control("resume"):
            return False
        result = self._send_media_key(self._vk("VK_MEDIA_PLAY_PAUSE"))
        self.logger.info("[MediaRouter] action=resume result=%s", result)
        return result

    def stop(self) -> bool:
        """Stop playback via pause toggle."""
        return self.pause()

    def next_track(self) -> bool:
        if not self._prepare_for_control("next"):
            return False
        result = self._send_media_key(self._vk("VK_MEDIA_NEXT_TRACK"))
        self.logger.info("[MediaRouter] action=next result=%s", result)
        return result

    def previous_track(self) -> bool:
        if not self._prepare_for_control("previous"):
            return False
        result = self._send_media_key(self._vk("VK_MEDIA_PREV_TRACK"))
        self.logger.info("[MediaRouter] action=previous result=%s", result)
        return result

    def adjust_volume(self, direction: str, *, steps: int = 2) -> bool:
        """Adjust system volume using media keys."""
        direction_lower = (direction or "").lower()
        if direction_lower.startswith("up") or "laut" in direction_lower:
            vk = self._vk("VK_VOLUME_UP")
        elif direction_lower.startswith("down") or "leise" in direction_lower:
            vk = self._vk("VK_VOLUME_DOWN")
        else:
            return False
        result = self._send_media_key(vk, repeat=max(1, int(steps)))
        self.logger.info("[MediaRouter] action=volume direction=%s result=%s", direction, result)
        return result

    def mute_toggle(self) -> bool:
        result = self._send_media_key(self._vk("VK_VOLUME_MUTE"))
        self.logger.info("[MediaRouter] action=mute result=%s", result)
        return result

    def last_state(self) -> Dict[str, Optional[str]]:
        return dict(self._last_state)

    def state(self) -> Dict[str, Any]:
        snapshot = dict(self._state)
        snapshot.update(self._last_state)
        return snapshot

    def refresh_state(self) -> Dict[str, Any]:
        """Re-scan running processes/windows to update YouTube activity flags."""
        edge_running = self._is_edge_running()
        youtube_window = self._find_youtube_window() if edge_running else None
        self._state["edge_running"] = edge_running
        self._state["youtube_window"] = bool(youtube_window)
        self._state["youtube_active"] = bool(youtube_window)
        if not youtube_window:
            # wenn kein aktives Fenster -> Track/URL nicht vertrauenswürdig
            self._last_state["target"] = self._last_state.get("target") or "youtube"
        return self.state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalize_target(self, target: Optional[str]) -> str:
        if not target:
            return "youtube"
        lowered = target.strip().lower()
        if lowered in {"yt", "youtube", "you tube", "music", "video"}:
            return "youtube"
        return lowered

    def _update_state(self, target: str, track: Optional[str], url: Optional[str], *, youtube_active: Optional[bool] = None) -> None:
        self._last_state["target"] = target
        self._last_state["track"] = track or self._last_state.get("track")
        self._last_state["url"] = url or self._last_state.get("url")
        if youtube_active is not None:
            self._state["youtube_active"] = bool(youtube_active)

    def _prepare_for_control(self, action: str) -> bool:
        edge_running = self._is_edge_running()
        self._state["edge_running"] = edge_running

        youtube_window = self._find_youtube_window()
        self._state["youtube_window"] = bool(youtube_window)

        if youtube_window:
            self._focus_window(youtube_window)
            self._state["youtube_active"] = True
            self.logger.info(
                "[MediaRouter] edge_running=%s youtube_tab=True action=%s", edge_running, action
            )
            return True

        if edge_running:
            self.logger.info(
                "[MediaRouter] edge_running=True youtube_tab=False action=%s", action
            )
            return False

        self.logger.info(
            "[MediaRouter] edge_running=False youtube_tab=False action=%s", action
        )
        self._state["youtube_active"] = False
        return False

    def _is_edge_running(self) -> bool:
        try:
            for proc in psutil.process_iter(["name"]):
                name = (proc.info.get("name") or "").lower()
                if name in {"msedge.exe", "edge.exe"}:
                    return True
        except Exception:
            pass
        return False

    def _find_youtube_window(self) -> Optional[int]:
        if not win32gui or not win32process:
            return None

        handles: list[int] = []

        def _enum_handler(hwnd: int, _param) -> None:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd) or ""
            if not title:
                return
            if "youtube" not in title.lower():
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                if proc.name().lower() not in {"msedge.exe", "edge.exe"}:
                    return
            except Exception:
                return
            handles.append(hwnd)

        try:
            win32gui.EnumWindows(_enum_handler, None)
        except Exception:
            return None
        if handles:
            return handles[0]
        return None

    def _focus_window(self, hwnd: int) -> bool:
        if not win32gui:
            return False
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            return True
        except Exception:
            return False

    def _send_media_key(self, vk_code: Optional[int], *, repeat: int = 1) -> bool:
        if vk_code is None:
            self.logger.warning("Media-Key-Steuerung ist nicht verfügbar (win32api fehlt).")
            return False
        if not win32api or not win32con:
            self.logger.warning("Media-Key-Steuerung erfordert pywin32 (win32api/win32con).")
            return False

        try:
            for _ in range(max(1, repeat)):
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            return True
        except Exception as exc:
            self.logger.error(f"Media-Key konnte nicht gesendet werden: {exc}")
            return False

    def _vk(self, name: str) -> Optional[int]:
        if not win32con:
            return None
        return getattr(win32con, name, None)
