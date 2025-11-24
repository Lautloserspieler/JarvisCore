"""Intent classification engine for J.A.R.V.I.S."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from utils.logger import Logger


@dataclass
class IntentDefinition:
    """Static description of an intent."""

    name: str
    handler: str
    priority: int = 50
    patterns: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    description: str = ""
    min_confidence: float = 0.35
    responses: List[str] = field(default_factory=list)


@dataclass
class IntentMatch:
    """Result of the intent classification."""

    name: str
    handler: str
    confidence: float
    entities: Dict[str, str] = field(default_factory=dict)
    matched_text: str = ""
    pattern: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    raw_text: str = ""
    normalized_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentEngine:
    """Scores and selects intents based on regex, keywords, and examples."""

    def __init__(
        self,
        *,
        config_path: Optional[Path] = None,
        logger: Optional[Logger] = None,
        default_confidence: float = 0.35,
    ) -> None:
        self.logger = logger or Logger()
        self.default_confidence = default_confidence
        self._compiled_patterns: Dict[str, List[re.Pattern[str]]] = {}
        self.intents: List[IntentDefinition] = []
        self._load_configuration(config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def match(self, text: str, *, context: Optional[Dict[str, Any]] = None) -> Optional[IntentMatch]:
        matches = self.rank(text, context=context, limit=1)
        return matches[0] if matches else None

    def rank(
        self,
        text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[IntentMatch]:
        text_raw = (text or "").strip()
        if not text_raw:
            return []
        text_normalized = self._normalize(text_raw)

        ranked: List[IntentMatch] = []
        for intent in self.intents:
            match = self._evaluate_intent(intent, text_raw, text_normalized)
            if match:
                ranked.append(match)

        ranked.sort(key=lambda item: (item.confidence, item.metadata.get("priority", 0)), reverse=True)
        if limit is not None:
            return ranked[:limit]
        return ranked

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def _load_configuration(self, config_path: Optional[Path]) -> None:
        source_description = "default intents"
        data: Dict[str, Any]
        if config_path:
            cfg_path = Path(config_path)
            if cfg_path.exists():
                try:
                    data = json.loads(cfg_path.read_text(encoding="utf-8"))
                    source_description = str(cfg_path)
                except Exception as exc:
                    self.logger.error(f"Failed to read intent config {cfg_path}: {exc}")
                    data = self._default_config()
            else:
                self.logger.warning(f"Intent config {cfg_path} not found, using defaults")
                data = self._default_config()
        else:
            data = self._default_config()

        self.default_confidence = float(data.get("default_confidence", self.default_confidence))

        intents: List[IntentDefinition] = []
        compiled: Dict[str, List[re.Pattern[str]]] = {}
        for entry in data.get("intents", []):
            try:
                intent = IntentDefinition(
                    name=str(entry["name"]),
                    handler=str(entry["handler"]),
                    priority=int(entry.get("priority", 50)),
                    patterns=list(entry.get("patterns", [])),
                    keywords=[kw.lower() for kw in entry.get("keywords", [])],
                    examples=list(entry.get("examples", [])),
                    description=str(entry.get("description", "")),
                    min_confidence=float(entry.get("min_confidence", entry.get("threshold", self.default_confidence))),
                    responses=list(entry.get("responses", [])),
                )
            except Exception as exc:
                self.logger.error(f"Invalid intent definition {entry}: {exc}")
                continue

            intents.append(intent)
            compiled[intent.name] = [self._compile_pattern(pat) for pat in intent.patterns if pat]

        if not intents:
            self.logger.warning("No intents loaded; falling back to defaults")
            fallback = self._default_config()
            intents = []
            compiled = {}
            for entry in fallback.get("intents", []):
                intent = IntentDefinition(
                    name=str(entry["name"]),
                    handler=str(entry["handler"]),
                    priority=int(entry.get("priority", 50)),
                    patterns=list(entry.get("patterns", [])),
                    keywords=[kw.lower() for kw in entry.get("keywords", [])],
                    examples=list(entry.get("examples", [])),
                    description=str(entry.get("description", "")),
                    min_confidence=float(entry.get("min_confidence", entry.get("threshold", self.default_confidence))),
                    responses=list(entry.get("responses", [])),
                )
                intents.append(intent)
                compiled[intent.name] = [self._compile_pattern(pat) for pat in intent.patterns if pat]

        self.intents = intents
        self._compiled_patterns = compiled
        self.logger.info(f"Intent engine initialised with {len(self.intents)} intents from {source_description}")

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _evaluate_intent(
        self,
        intent: IntentDefinition,
        text_raw: str,
        text_normalized: str,
    ) -> Optional[IntentMatch]:
        regex_score, regex_info = self._score_regex(intent, text_raw)
        keyword_score, keyword_hits = self._score_keywords(intent, text_normalized)
        similarity_score, best_example = self._score_examples(intent, text_normalized)
        priority_bonus = min(max(intent.priority, 0), 100) / 100.0 * 0.1

        score = regex_score + keyword_score + similarity_score + priority_bonus
        score = min(score, 0.99)

        threshold = max(intent.min_confidence, self.default_confidence)
        if score < threshold:
            return None

        entities = self._extract_entities(regex_info.get("match"), text_raw)
        metadata = {
            "priority": intent.priority,
            "keyword_hits": keyword_hits,
            "example_similarity": best_example,
            "regex_score": regex_score,
            "keyword_score": keyword_score,
            "similarity_score": similarity_score,
        }
        match = IntentMatch(
            name=intent.name,
            handler=intent.handler,
            confidence=score,
            entities=entities,
            matched_text=regex_info.get("matched_text", ""),
            pattern=regex_info.get("pattern"),
            keywords=[kw for kw in intent.keywords if kw in text_normalized],
            raw_text=text_raw,
            normalized_text=text_normalized,
            metadata=metadata,
        )
        return match

    def _score_regex(self, intent: IntentDefinition, text_raw: str) -> (float, Dict[str, Any]):
        patterns = self._compiled_patterns.get(intent.name, [])
        best_score = 0.0
        best_info: Dict[str, Any] = {}
        if not patterns:
            return 0.0, best_info

        stripped = text_raw.strip()
        base_length = max(len(stripped), 1)

        for pattern in patterns:
            match = pattern.search(text_raw)
            if not match:
                continue
            matched_text = match.group(0)
            coverage = len(matched_text.strip()) / base_length
            score = 0.55 + 0.35 * min(coverage, 1.0)
            if score > best_score:
                best_score = score
                best_info = {
                    "pattern": pattern.pattern,
                    "match": match,
                    "matched_text": matched_text,
                }
        return best_score, best_info

    def _score_keywords(self, intent: IntentDefinition, text_normalized: str) -> (float, int):
        if not intent.keywords:
            return 0.0, 0
        hits = 0
        for keyword in intent.keywords:
            if keyword and keyword in text_normalized:
                hits += 1
        if not hits:
            return 0.0, 0
        ratio = hits / len(intent.keywords)
        score = 0.18 + 0.12 * min(ratio, 1.0)
        return score, hits

    def _score_examples(self, intent: IntentDefinition, text_normalized: str) -> (float, float):
        if not intent.examples:
            return 0.0, 0.0
        best_ratio = 0.0
        for example in intent.examples:
            example_norm = self._normalize(example)
            ratio = difflib.SequenceMatcher(None, text_normalized, example_norm).ratio()
            best_ratio = max(best_ratio, ratio)
        if best_ratio <= 0.5:
            return 0.0, best_ratio
        return 0.2 * best_ratio, best_ratio

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_entities(self, match: Optional[re.Match[str]], original_text: str) -> Dict[str, str]:
        if not match:
            return {}
        entities: Dict[str, str] = {}
        for key, value in match.groupdict().items():
            if not value:
                continue
            entities[key] = self._clean_entity_value(value)
        if not entities:
            return {}
        return entities

    @staticmethod
    def _clean_entity_value(value: str) -> str:
        cleaned = value.strip()
        for filler in ("den", "das", "die", "ein", "eine", "ueber", "ueber", "nach"):
            if cleaned.lower().startswith(filler + " "):
                cleaned = cleaned[len(filler) + 1 :].strip()
        return cleaned

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only).strip().lower()

    @staticmethod
    def _compile_pattern(pattern: str) -> re.Pattern[str]:
        return re.compile(pattern, flags=re.IGNORECASE)

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            "intents": [
                {
                    "name": "greeting",
                    "handler": "handle_greeting",
                    "priority": 80,
                    "patterns": ["(?:^|\\b)(hallo|hi|hey)\\b"],
                    "keywords": ["hallo", "hi", "hey"],
                    "examples": ["hallo jarvis"],
                    "description": "Fallback Begruessung",
                },
                {
                    "name": "help",
                    "handler": "handle_help",
                    "priority": 40,
                    "patterns": ["hilfe"],
                    "keywords": ["hilfe"],
                    "examples": ["hilfe"],
                    "description": "Fallback Hilfe",
                },
            ]
        }


__all__ = ["IntentEngine", "IntentDefinition", "IntentMatch"]
