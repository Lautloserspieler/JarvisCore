"""Slang/Umgangssprache-Normalisierung für deutschsprachige Eingaben.

Einfache, erweiterbare Vorverarbeitungsschicht vor der Intent-Engine.
"""
from __future__ import annotations

import re
from typing import Dict


class TextNormalizer:
    """Normiert umgangssprachliche Ausdrücke und Rechtschreibvarianten.

    Diese Implementierung ist leichtgewichtig und regelbasiert. Sie kann
    später durch ML-Modelle oder konfigurierbare Wörterbücher erweitert werden.
    """

    def __init__(self, slang_map: Optional[Dict[str, str]] = None) -> None:
        # Basis-Slang/Wortersetzungen (deutsch, inkl. häufiger Chat/Umgangsformen)
        base_map: Dict[str, str] = {
            "moin": "hallo",
            "servus": "hallo",
            "tach": "hallo",
            "yo": "hallo",
            "jo": "ja",
            "joo": "ja",
            "nope": "nein",
            "no": "nein",
            "pls": "bitte",
            "plz": "bitte",
            "thx": "danke",
            "danke dir": "danke",
            "btw": "uebrigens",
            "kp": "kein plan",
            "kA": "kein plan",
            "ka": "kein plan",
            "idk": "ich weiss nicht",
            "kk": "ok",
            "okey": "ok",
            "okay": "ok",
            "k": "ok",
            "bin am": "ich",
            "mach ma": "mache bitte",
            "mach mal": "mache bitte",
            "öffne mal": "oeffne",
            "mach mal auf": "oeffne",
            "mach auf": "oeffne",
            "zeig mal": "zeige",
            "zeig ma": "zeige",
            "sag ma": "sage",
            "sag mal": "sage",
        }
        if slang_map:
            base_map.update(slang_map)
        # Re-compile to word-boundary patterns for safe replacements
        self._patterns = [
            (re.compile(rf"\b{re.escape(src)}\b", flags=re.IGNORECASE), dst)
            for src, dst in sorted(base_map.items(), key=lambda x: -len(x[0]))
        ]
        # Normalize multiple spaces
        self._space_re = re.compile(r"\s+")

    def normalize(self, text: str) -> str:
        if not text:
            return text
        normalized = text.strip()
        # Apply replacements
        for pat, repl in self._patterns:
            normalized = pat.sub(repl, normalized)
        # Collapse spaces
        normalized = self._space_re.sub(" ", normalized).strip()
        return normalized


__all__ = ["TextNormalizer"]
