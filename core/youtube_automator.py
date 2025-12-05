"""Automates launching YouTube playback via Microsoft Edge."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple

import requests

from utils.logger import Logger


class YouTubeAutomator:
    """Searches and launches YouTube playback in Microsoft Edge."""

    _VIDEO_ID_PATTERN = re.compile(r'"videoId":"(?P<video_id>[-_a-zA-Z0-9]{11})"')

    def __init__(self, *, settings: Optional[object] = None) -> None:
        self.logger = Logger()
        self.settings = settings
        self._edge_path = self._detect_edge()
        self._launch_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def play_track(self, track: str) -> Tuple[bool, Optional[str], bool]:
        """
        Resolve the given track on YouTube and launch playback.

        Returns ``(launched, url, exact_match)``.
        """
        cleaned = (track or "").strip()
        if not cleaned:
            return False, None, False

        search_url = self._build_search_url(cleaned)
        video_url = None
        try:
            video_url = self._resolve_top_result(cleaned)
        except Exception as exc:  # pragma: no cover
            self.logger.debug(f"Konnte YouTube-Ergebnis nicht auflösen: {exc}")
            video_url = None

        target_url = video_url or search_url
        launched = self._launch_edge(target_url)
        exact = bool(video_url)
        if launched and not exact:
            self.logger.info("YouTube-Suchseite geöffnet (kein direktes Video gefunden).")
        return launched, target_url, exact

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_search_url(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        return f"https://www.youtube.com/results?search_query={encoded}"

    def _resolve_top_result(self, query: str) -> Optional[str]:
        """Fetch the search page and extract the first video ID."""
        url = self._build_search_url(query)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        text = response.text

        # Attempt structured extraction first
        initial_data = self._extract_yt_initial_data(text)
        if initial_data:
            video_id = self._extract_first_video_from_initial_data(initial_data)
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        # Fallback regex scan
        match = self._VIDEO_ID_PATTERN.search(text)
        if match:
            video_id = match.group("video_id")
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    def _extract_yt_initial_data(self, html: str) -> Optional[dict]:
        """Parse the ytInitialData JSON blob if available."""
        marker = "ytInitialData"
        idx = html.find(marker)
        if idx == -1:
            return None
        start = html.find("{", idx)
        end = html.find("};", start)
        if start == -1 or end == -1:
            return None
        try:
            json_text = html[start : end + 1]
            return json.loads(json_text)
        except Exception:
            return None

    def _extract_first_video_from_initial_data(self, data: dict) -> Optional[str]:
        try:
            contents = (
                data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
            )
        except Exception:
            return None
        for section in contents:
            try:
                items = section["itemSectionRenderer"]["contents"]
            except Exception:
                continue
            for item in items:
                video_renderer = item.get("videoRenderer")
                if not video_renderer:
                    continue
                video_id = video_renderer.get("videoId")
                if video_id:
                    return str(video_id)
        return None

    def _detect_edge(self) -> Optional[str]:
        """Locate the Edge executable."""
        possible_paths = [
            Path(p)
            for p in (
                shutil.which("msedge"),
                shutil.which("msedge.exe"),
                shutil.which("microsoft-edge"),
            )
        ]
        for candidate in possible_paths:
            if candidate.exists():
                return str(candidate)
        try:
            import shutil

            located = shutil.which("msedge")
            if located:
                return located
        except Exception:
            pass
        return None

    def _launch_edge(self, url: str) -> bool:
        """Launch Microsoft Edge with the given URL."""
        if not url:
            return False
        edge_path = self._edge_path
        args = [url]

        profile_arg = self._edge_profile_argument()
        if profile_arg:
            args.insert(0, profile_arg)

        try:
            creation_flags = 0
            try:
                creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
            except AttributeError:
                creation_flags = 0

            with self._launch_lock:
                if edge_path:
                    subprocess.Popen(
                        [edge_path, *args],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creation_flags,
                    )
                else:
                    # Fallback: rely on PATH via "start msedge"
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", "msedge", *args],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            # kurze Verzögerung, damit der Browser starten kann
            time.sleep(0.2)
            return True
        except Exception as exc:
            self.logger.error(f"Edge konnte nicht gestartet werden: {exc}")
            return False

    def _edge_profile_argument(self) -> Optional[str]:
        """Return a profile directory argument if configured."""
        if not self.settings:
            return None
        try:
            media_settings = self.settings.get("media", {})  # type: ignore[attr-defined]
        except Exception:
            media_settings = {}
        if not isinstance(media_settings, dict):
            return None
        youtube_cfg = media_settings.get("youtube", {})
        if not isinstance(youtube_cfg, dict):
            return None
        profile_dir = youtube_cfg.get("edge_profile_directory")
        if isinstance(profile_dir, str) and profile_dir.strip():
            # Edge expects --profile-directory=<name>
            return f"--profile-directory={profile_dir.strip()}"
        user_data_dir = youtube_cfg.get("edge_user_data_dir")
        if isinstance(user_data_dir, str) and user_data_dir.strip():
            return f"--user-data-dir={user_data_dir.strip()}"
        return None
