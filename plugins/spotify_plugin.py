"""Spotify Plugin for JARVIS - Spotify Desktop-App oder Web-API steuern"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import time
import webbrowser
from typing import Any, Dict, Optional, Tuple

import psutil
import requests

from utils.media_command_parser import MediaPreferences, parse_media_command

# Plugin Metadata
PLUGIN_NAME = "Spotify"
PLUGIN_DESCRIPTION = "Steuert Spotify per Desktop-App oder Web-API"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class SpotifyPlugin:
    """Plugin für Spotify-Steuerung."""

    def __init__(self) -> None:
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        self.pkce_verifier = os.getenv("SPOTIFY_PKCE_VERIFIER")
        self.auth_code = os.getenv("SPOTIFY_AUTH_CODE")

    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        command_lower = command.lower().strip()

        prefs = MediaPreferences()
        parsed = parse_media_command(command_lower, prefs)

        if parsed.target == "youtube":
            return None

        if not self._is_spotify_request(command_lower) and parsed.target != "spotify":
            return None

        intent = self._detect_intent(command_lower, parsed)
        query, explicit_uri = self._extract_query_and_uri(command, parsed)

        favorite_payload: Dict[str, Optional[str]] = {}
        if parsed.favorite_song:
            favorite_payload = prefs.get_favorite_song("spotify")
            if not favorite_payload.get("query") and not favorite_payload.get("uri"):
                favorite_payload = self._hydrate_spotify_favorite_song(prefs) or favorite_payload
        elif parsed.favorite_playlist:
            favorite_payload = prefs.get_favorite_playlist("spotify")
            if not favorite_payload.get("name") and not favorite_payload.get("uri"):
                favorite_payload = self._hydrate_spotify_favorite_playlist(prefs) or favorite_payload

        if not explicit_uri and favorite_payload.get("uri"):
            explicit_uri = favorite_payload["uri"]
        if not query:
            query = favorite_payload.get("query") or favorite_payload.get("name") or ""

        if (parsed.favorite_song or parsed.favorite_playlist) and not query and not explicit_uri:
            return (
                "Ich habe noch keinen Favoriten hinterlegt. "
                "Bitte trage ihn in data/user_media_prefs.json ein oder aktiviere die Spotify-API."
            )

        target_uri = explicit_uri

        if not target_uri and query:
            target_uri = self._resolve_uri_via_api(query, intent)

        app_available = self._is_spotify_running()
        if not app_available:
            app_available = self._start_spotify_app()

        if app_available:
            return self._open_in_app(target_uri, query, intent)

        return self._play_via_api(target_uri, query, intent)

    def _is_spotify_request(self, command: str) -> bool:
        triggers = [
            "spotify",
            "spiel",
            "spiele",
            "playlist",
            "song",
            "lied",
            "lieblingssong",
            "lieblingslied",
            "lieblingsplaylist",
        ]
        return any(trigger in command for trigger in triggers)

    def _detect_intent(self, command: str, parsed) -> str:
        if parsed.favorite_playlist or parsed.playlist_name or "playlist" in command:
            return "playlist"
        return "track"

    def _extract_query_and_uri(self, command: str, parsed) -> Tuple[str, Optional[str]]:
        uri_match = re.search(r"spotify:(track|playlist):[\w]+", command)
        if uri_match:
            return "", uri_match.group(0)

        url_match = re.search(r"open\.spotify\.com/(track|playlist)/([\w]+)", command)
        if url_match:
            return "", f"spotify:{url_match.group(1)}:{url_match.group(2)}"

        if parsed.playlist_name:
            return parsed.playlist_name, None

        cleaned = command
        cleaned = re.sub(r"\bspiel(?:e)?\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bbitte\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bplaylist\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\blieblings(?:song|lied)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\blieblingsplaylist\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned, None

    def _is_spotify_running(self) -> bool:
        target_names = {"spotify.exe", "spotify"}
        for process in psutil.process_iter(["name", "cmdline"]):
            try:
                name = (process.info.get("name") or "").lower()
                if name in target_names:
                    return True
                cmdline = process.info.get("cmdline") or []
                if any("spotify" in (entry or "").lower() for entry in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _start_spotify_app(self) -> bool:
        system_name = platform.system().lower()
        if system_name == "windows":
            command = "start spotify"
            shell = True
        elif system_name == "darwin":
            command = "open -a Spotify"
            shell = True
        else:
            command = "spotify"
            shell = False

        try:
            subprocess.Popen(command, shell=shell)
        except Exception:
            return False

        time.sleep(1.5)
        return self._is_spotify_running()

    def _open_in_app(self, uri: Optional[str], query: str, intent: str) -> str:
        if uri:
            webbrowser.open(uri)
            return "🎵 Öffne Spotify in der Desktop-App."

        if query:
            search_uri = f"spotify:search:{query}"
            webbrowser.open(search_uri)
            return f"🔎 Öffne die Spotify-Suche für: {query}"

        if intent == "playlist":
            return "ℹ️ Bitte nenne eine Playlist oder sende einen Spotify-Link."

        return "ℹ️ Bitte nenne einen Songtitel oder sende einen Spotify-Link."

    def _resolve_uri_via_api(self, query: str, intent: str) -> Optional[str]:
        token = self._get_access_token()
        if not token:
            return None

        search_type = "playlist" if intent == "playlist" else "track"
        params = {
            "q": query,
            "type": search_type,
            "limit": 1,
        }
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get(f"{search_type}s", {}).get("items", [])
            if items:
                return items[0].get("uri")
        except requests.RequestException:
            return None
        return None

    def _play_via_api(self, uri: Optional[str], query: str, intent: str) -> str:
        token = self._get_access_token()
        if not token:
            return (
                "⚠️ Spotify Web-API nicht konfiguriert. Bitte setze Spotify-Credentials "
                "(Client ID/Secret + Refresh Token oder PKCE) in den Einstellungen."
            )

        target_uri = uri
        if not target_uri and query:
            target_uri = self._resolve_uri_via_api(query, intent)

        if not target_uri:
            return "❌ Konnte kein passendes Spotify-Ergebnis finden."

        payload: Dict[str, Any]
        if intent == "playlist" or target_uri.startswith("spotify:playlist"):
            payload = {"context_uri": target_uri}
        else:
            payload = {"uris": [target_uri]}

        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.put(
                "https://api.spotify.com/v1/me/player/play",
                json=payload,
                headers=headers,
                timeout=10,
            )
            if response.status_code == 404:
                return "⚠️ Kein aktives Spotify-Gerät gefunden. Bitte Spotify öffnen und erneut versuchen."
            response.raise_for_status()
            return "▶️ Spotify-Wiedergabe gestartet."
        except requests.RequestException as exc:
            return f"❌ Fehler beim Start der Wiedergabe: {exc}"

    def _get_access_token(self) -> Optional[str]:
        if not self.client_id:
            return None

        token_url = "https://accounts.spotify.com/api/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data: Dict[str, str]

        if self.refresh_token:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
            }
        elif self.auth_code and self.redirect_uri and self.pkce_verifier:
            data = {
                "grant_type": "authorization_code",
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "code_verifier": self.pkce_verifier,
            }
        else:
            return None

        auth = None
        if self.client_secret:
            auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(token_url, data=data, headers=headers, auth=auth, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return payload.get("access_token")
        except requests.RequestException:
            return None

    def _hydrate_spotify_favorite_song(self, prefs: MediaPreferences) -> Optional[Dict[str, Optional[str]]]:
        token = self._get_access_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get("https://api.spotify.com/v1/me/tracks", params={"limit": 1}, headers=headers, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return None
        items = payload.get("items", [])
        if not items:
            return None
        track = items[0].get("track") if isinstance(items[0], dict) else None
        if not isinstance(track, dict):
            return None
        uri = track.get("uri")
        name = track.get("name") or ""
        artists = track.get("artists") if isinstance(track.get("artists"), list) else []
        artist_name = ""
        if artists and isinstance(artists[0], dict):
            artist_name = artists[0].get("name") or ""
        query = " ".join(part for part in [name, artist_name] if part).strip()
        if not uri and not query:
            return None
        prefs.set_favorite_song("spotify", query=query or None, uri=uri)
        return {"query": query or None, "uri": uri}

    def _hydrate_spotify_favorite_playlist(self, prefs: MediaPreferences) -> Optional[Dict[str, Optional[str]]]:
        token = self._get_access_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get("https://api.spotify.com/v1/me/playlists", params={"limit": 1}, headers=headers, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return None
        items = payload.get("items", [])
        if not items:
            return None
        playlist = items[0] if isinstance(items[0], dict) else None
        if not isinstance(playlist, dict):
            return None
        name = playlist.get("name")
        uri = playlist.get("uri")
        if not name and not uri:
            return None
        prefs.set_favorite_playlist("spotify", name=name, uri=uri)
        return {"name": name, "uri": uri}


# Plugin Instance

def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    plugin = SpotifyPlugin()
    return plugin.process(command, context)


def health_check() -> Dict[str, Any]:
    """Health-Check für das Spotify-Plugin."""
    missing = []
    if not os.getenv("SPOTIFY_CLIENT_ID"):
        missing.append("spotify_client_id")
    if not os.getenv("SPOTIFY_REFRESH_TOKEN"):
        missing.append("spotify_refresh_token")
    return {
        "status": "ok",
        "missing_keys": missing,
        "errors": [],
    }
