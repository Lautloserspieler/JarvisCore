"""Utilities for generating command hotwords and intent hints."""

from __future__ import annotations

import difflib
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from utils.logger import Logger


class HotwordManager:
    """Collects speech hotwords, synonyms, and intent hints dynamically."""

    BASE_COMMAND_WORDS: Sequence[str] = (
        "öffne",
        "oeffne",
        "starte",
        "starten",
        "mach auf",
        "beende",
        "schließe",
        "schliesse",
        "stoppe",
        "stopp",
        "halte an",
        "spiele",
        "spiel",
        "spiele musik",
        "musik abspielen",
        "pause",
        "pausiere",
        "lauter",
        "leiser",
        "lautstärke hoch",
        "lautstaerke hoch",
        "lautstärke runter",
        "lautstaerke runter",
        "suche",
        "finde",
        "zeige",
        "zeige status",
        "zeig mir",
        "wie spät",
        "wie spaet",
        "zeit",
        "datum",
        "notfall",
        "notfallprotokoll",
        "notfall protokoll",
        "alarmmodus",
        "sicherheitsmodus",
        "alarm ausloesen",
        "alarm auslösen",
    )

    INTENT_HINT_CONFIG: Dict[str, Dict[str, object]] = {
        "open_program": {
            "keywords": (
                "öffne",
                "oeffne",
                "mach auf",
                "öffnen",
                "oeffnen",
                "starte",
                "starten",
                "programm starten",
                "application öffnen",
                "application oeffnen",
            ),
            "hint": "intent_open_program",
            "boost": 0.18,
        },
        "close_program": {
            "keywords": (
                "schließe",
                "schliesse",
                "mach zu",
                "beende",
                "programm schließen",
                "programm schliessen",
                "stoppe programm",
            ),
            "hint": "intent_close_program",
            "boost": 0.16,
        },
        "knowledge_search": {
            "keywords": (
                "suche",
                "finde",
                "recherchiere",
                "informationen über",
                "informationen ueber",
                "google",
                "was ist",
                "wer ist",
            ),
            "hint": "intent_knowledge_search",
            "boost": 0.12,
        },
        "time_query": {
            "keywords": (
                "zeit",
                "uhrzeit",
                "wie spät",
                "wie spaet",
                "wie viel uhr",
            ),
            "hint": "intent_time_query",
            "boost": 0.1,
        },
        "date_query": {
            "keywords": (
                "datum",
                "welcher tag",
                "welches datum",
                "heute welches datum",
            ),
            "hint": "intent_date_query",
            "boost": 0.1,
        },
        "volume_up": {
            "keywords": (
                "lauter",
                "lautstärke hoch",
                "lautstaerke hoch",
                "lautstärke erhöhen",
                "lautstaerke erhoehen",
                "erhöhe lautstärke",
            ),
            "hint": "intent_volume_up",
            "boost": 0.12,
        },
        "volume_down": {
            "keywords": (
                "leiser",
                "lautstärke runter",
                "lautstaerke runter",
                "senke lautstärke",
                "lautstärke verringern",
            ),
            "hint": "intent_volume_down",
            "boost": 0.12,
        },
        "play_media": {
            "keywords": (
                "spiele musik",
                "spiel musik",
                "spiele lied",
                "musik abspielen",
                "song abspielen",
            ),
            "hint": "intent_play_media",
            "boost": 0.14,
        },
        "stop_media": {
            "keywords": (
                "stopp",
                "stoppe",
                "halte an",
                "musik aus",
                "musik stoppen",
            ),
            "hint": "intent_stop_media",
            "boost": 0.14,
        },
        "emergency_protocol": {
            "keywords": (
                "notfall",
                "notfallprotokoll",
                "notfall protokoll",
                "alarmmodus",
                "sicherheitsmodus",
                "stufe 1",
                "stufe 2",
                "stufe 3",
            ),
            "hint": "intent_emergency_protocol",
            "boost": 0.2,
        },
    }

    FILLER_WORDS: Set[str] = {"und", "aber", "also", "äh", "ähm", "hm", "naja"}

    SHORT_COMMAND_WHITELIST: Set[str] = {"stopp", "stop", "halt", "pause", "ja", "nein", "hi", "hallo"}

    SUPPORTED_START_SUFFIXES: Sequence[str] = (".lnk", ".url", ".appref-ms", ".exe")

    def __init__(self, settings: Optional[object] = None) -> None:
        self.logger = Logger()
        self.settings = settings
        self._hotword_cache: Optional[List[str]] = None
        self._program_hotwords: Optional[List[str]] = None
        self._intent_hint_cache: Optional[Dict[str, Dict[str, object]]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_hotwords(self) -> List[str]:
        if self._hotword_cache is not None:
            return list(self._hotword_cache)

        collected: Set[str] = set()
        collected.update(self._normalise_many(self.BASE_COMMAND_WORDS))
        collected.update(self._collect_settings_hotwords())
        collected.update(self._discover_program_hotwords())

        hotwords = sorted(word for word in collected if word)
        self._hotword_cache = hotwords
        return list(hotwords)

    def get_program_hotwords(self) -> List[str]:
        if self._program_hotwords is None:
            program_words = self._discover_program_hotwords()
            self._program_hotwords = sorted(word for word in program_words if word)
        return list(self._program_hotwords)

    def get_intent_hint_config(self) -> Dict[str, Dict[str, object]]:
        if self._intent_hint_cache is not None:
            return {key: dict(value) for key, value in self._intent_hint_cache.items()}
        config: Dict[str, Dict[str, object]] = {}
        for key, data in self.INTENT_HINT_CONFIG.items():
            config[key] = {
                "keywords": tuple(self._normalise_many(data.get("keywords", []))),
                "hint": str(data.get("hint") or key),
                "boost": float(data.get("boost") or 0.0),
            }

        # Merge custom overrides from settings, if present
        overrides = self._get_settings_synonyms()
        if overrides:
            for intent, words in overrides.items():
                normalized_intent = str(intent).strip()
                if not normalized_intent:
                    continue
                bucket = config.setdefault(normalized_intent, {"keywords": tuple(), "hint": f"intent_{normalized_intent}", "boost": 0.1})
                existing = set(bucket.get("keywords", ()))
                existing.update(self._normalise_many(words))
                bucket["keywords"] = tuple(sorted(existing))
        self._intent_hint_cache = config
        return {key: dict(value) for key, value in config.items()}

    def get_filler_words(self) -> Set[str]:
        return set(self.FILLER_WORDS)

    def get_short_command_whitelist(self) -> Set[str]:
        return set(self.SHORT_COMMAND_WHITELIST)

    def merge_hotwords(self, existing: Optional[Iterable[str]]) -> List[str]:
        combined: Set[str] = set()
        combined.update(self.get_hotwords())
        combined.update(self._normalise_many(existing or ()))
        return sorted(word for word in combined if word)

    def build_initial_prompt(self, base_prompt: str, hotwords: Sequence[str]) -> str:
        """Append frequently used command examples to the initial prompt."""
        prompt = (base_prompt or "").strip()
        if not hotwords:
            return prompt or ""

        examples = []
        for word in hotwords:
            if not word or " " not in word:
                continue
            if any(word.startswith(prefix) for prefix in ("intent_", "command_", "programm ")):
                continue
            examples.append(word)
            if len(examples) >= 10:
                break

        if not examples:
            examples = hotwords[:10]

        addition = " Typische Kurzbefehle: " + ", ".join(examples[:12]) + "."
        if addition.strip() and addition.strip(".") not in prompt:
            prompt = f"{prompt.rstrip('.')}." if prompt and not prompt.endswith(".") else prompt
            prompt = f"{prompt}{addition}" if prompt else addition.strip()
        return prompt.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalise_word(self, word: str) -> str:
        text = (word or "").strip().lower()
        if not text:
            return ""
        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
        }
        for src, target in replacements.items():
            text = text.replace(src, target)
        text = re.sub(r"[^\w\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalise_many(self, words: Iterable[str]) -> Set[str]:
        return {self._normalise_word(word) for word in (words or []) if self._normalise_word(word)}

    def _collect_settings_hotwords(self) -> Set[str]:
        if not self.settings:
            return set()
        try:
            custom = self.settings.get("speech.command_hotwords", [])  # type: ignore[attr-defined]
        except Exception:
            custom = []
        if not isinstance(custom, (list, tuple, set)):
            return set()
        return self._normalise_many(custom)

    def _get_settings_synonyms(self) -> Dict[str, Sequence[str]]:
        if not self.settings:
            return {}
        try:
            synonyms = self.settings.get("speech.command_synonyms", {})  # type: ignore[attr-defined]
        except Exception:
            synonyms = {}
        if not isinstance(synonyms, dict):
            return {}
        filtered: Dict[str, Sequence[str]] = {}
        for key, values in synonyms.items():
            if isinstance(values, (list, tuple, set)):
                filtered[str(key)] = list(values)
        return filtered

    def _discover_program_hotwords(self) -> Set[str]:
        program_names: Set[str] = set()
        # Add names from settings (if any)
        try:
            custom_programs = self.settings.get("speech.preferred_programs", []) if self.settings else []
        except Exception:
            custom_programs = []
        program_names.update(self._normalise_many(custom_programs or []))

        if os.name == "nt":
            program_names.update(self._collect_windows_shortcuts())
        return program_names

    def _collect_windows_shortcuts(self) -> Set[str]:
        collected: Set[str] = set()
        appdata = Path(os.environ.get("APPDATA", "")).resolve()
        programdata = Path(os.environ.get("PROGRAMDATA", "")).resolve()
        candidates = [
            appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            programdata / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]
        for base in candidates:
            if not base.exists():
                continue
            try:
                for entry in base.rglob("*"):
                    if not entry.is_file():
                        continue
                    if entry.suffix.lower() not in self.SUPPORTED_START_SUFFIXES:
                        continue
                    normalized = self._normalise_word(entry.stem)
                    if not normalized or len(normalized) <= 2:
                        continue
                    collected.add(normalized)
            except Exception as exc:
                self.logger.debug(f"Startmenü-Scan fehlgeschlagen: {exc}")
        return set(sorted(collected)[:64])

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------
    @staticmethod
    def approximate_contains(text: str, alias: str, *, cutoff: float = 0.86) -> bool:
        if not text or not alias:
            return False
        if alias in text:
            return True
        words = text.split()
        alias_words = alias.split()
        if len(alias_words) == 1:
            target = alias_words[0]
            for word in words:
                if len(word) < 3:
                    continue
                if difflib.SequenceMatcher(None, word, target).ratio() >= cutoff:
                    return True
            return False
        # Multi-word alias: check subsequences
        for index in range(len(words) - len(alias_words) + 1):
            window = " ".join(words[index : index + len(alias_words)])
            if difflib.SequenceMatcher(None, window, alias).ratio() >= cutoff:
                return True
        return False
