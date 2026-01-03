"""YouTube Plugin für JARVIS - YouTube/YouTube Music Wiedergabe starten."""

from __future__ import annotations

import re
from typing import Dict, Any, Optional, Tuple

from core.youtube_automator import YouTubeAutomator

# Plugin Metadata
PLUGIN_NAME = "YouTube"
PLUGIN_DESCRIPTION = "Startet YouTube/YouTube Music Wiedergabe für Videos oder Audio"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class YouTubePlugin:
    """Plugin für YouTube-Befehle (Audio/Video, Qualitätspräferenz)."""

    _QUALITY_HINTS = {
        "2160": "hd2160",
        "1440": "hd1440",
        "1080": "hd1080",
        "720": "hd720",
        "480": "large",
        "360": "medium",
        "240": "small",
    }

    def __init__(self) -> None:
        self.automator = YouTubeAutomator()

    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        command_lower = (command or "").lower().strip()

        if not self._is_youtube_request(command_lower):
            return None

        mode = self._detect_mode(command_lower)
        quality_label, quality_hint = self._extract_quality(command_lower)
        query = self._extract_query(command)

        if not query:
            return "Bitte nenne einen Titel oder Suchbegriff für YouTube."

        launched, url, exact = self.automator.play_track(
            query,
            mode=mode,
            quality_hint=quality_hint,
        )

        if launched:
            if mode == "audio":
                if exact:
                    response = f"Starte YouTube Music für '{query}'."
                else:
                    response = f"Ich öffne YouTube Music für '{query}'."
            else:
                if exact:
                    response = f"Starte YouTube-Video für '{query}'."
                else:
                    response = f"Ich öffne die YouTube-Suche nach '{query}'."
        else:
            response = "YouTube konnte nicht gestartet werden."

        response_parts = [response]
        if quality_label:
            if mode == "audio":
                response_parts.append(
                    f"Hinweis: Qualitätswunsch {quality_label} gilt nur für Video."
                )
            else:
                response_parts.append(
                    f"Qualitätswunsch: {quality_label} (Hint vq={quality_hint})."
                )
        if launched and not exact:
            response_parts.append("Hinweis: Kein direktes Video gefunden.")
        if not launched:
            edge_status = "Edge gefunden" if self.automator.edge_available() else "Edge nicht gefunden"
            response_parts.append(f"Status: {edge_status}.")
        if url:
            response_parts.append(f"URL: {url}")

        return " ".join(response_parts)

    def _is_youtube_request(self, command_lower: str) -> bool:
        media_terms = [
            "youtube",
            "you tube",
            "yt",
            "video",
            "audio",
            "musik",
            "song",
            "lied",
            "titel",
            "track",
            "playlist",
        ]
        play_verbs = ["spiel", "spiele", "abspielen", "starte", "play"]
        if any(term in command_lower for term in media_terms) and any(
            verb in command_lower for verb in play_verbs
        ):
            return True
        return "youtube" in command_lower or "you tube" in command_lower

    def _detect_mode(self, command_lower: str) -> str:
        if "nur audio" in command_lower or "audio only" in command_lower or "audio-only" in command_lower:
            return "audio"
        if "mit video" in command_lower:
            return "video"
        if "video" in command_lower:
            return "video"
        if "audio" in command_lower or "musik" in command_lower:
            return "audio"
        return "video"

    def _extract_quality(self, command_lower: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r"\b(2160|1440|1080|720|480|360|240)p\b", command_lower)
        if not match:
            return None, None
        resolution = match.group(1)
        hint = self._QUALITY_HINTS.get(resolution)
        if not hint:
            return None, None
        return f"{resolution}p", hint

    def _extract_query(self, command: str) -> str:
        cleaned = command
        patterns = [
            r"(?i)\b(spiel(?:e|en|t)?|abspielen|starte|play(?:e)?)\b",
            r"(?i)\b(auf|bei|von)\s+(youtube|you\s*tube|yt)\b",
            r"(?i)\b(youtube|you\s*tube|yt)\b",
            r"(?i)\b(nur\s+audio|mit\s+video|audio|video|musik|song|lied|titel|track|playlist)\b",
            r"(?i)\b(2160|1440|1080|720|480|360|240)p\b",
            r"(?i)\b(bitte|mir|mal)\b",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:,.")
        return cleaned


_plugin_instance: Optional[YouTubePlugin] = None


def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für das JARVIS Plugin-System."""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = YouTubePlugin()
    return _plugin_instance.process(command, context)


def get_plugin_instance() -> YouTubePlugin:
    """Gibt die Plugin-Instanz zurück."""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = YouTubePlugin()
    return _plugin_instance


def health_check() -> Dict[str, Any]:
    """Health-Check für das YouTube-Plugin."""
    automator = YouTubeAutomator()
    missing_keys = []
    if not automator.edge_available():
        missing_keys.append("edge")
    status = "ok" if not missing_keys else "warning"
    return {
        "status": status,
        "missing_keys": missing_keys,
        "errors": [],
    }
