"""
LLM-Manager fuer J.A.R.V.I.S.
Verwaltet lokale Sprachmodelle (Mistral, DeepSeek, Qwen, Llama, etc.)
"""

import os
import json
import shutil
import threading
import time
import random
import hashlib
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Callable

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from llama_cpp import Llama
except ImportError:  # pragma: no cover
    Llama = None

from utils.logger import Logger
from core.llm_router import LLMRouter


class LLMManager:
    """Verwaltet lokale Large Language Models und uebernimmt Modellwahl."""

    def __init__(self, settings: Optional[object] = None) -> None:
        self.logger = Logger()
        self.settings = settings
        # Prefer GPU by default unless explicitly disabled via env
        import os as _os_env_init
        _os_env_init.environ.setdefault("LLAMA_USE_GPU", "1")
        _os_env_init.environ.setdefault("LLAMA_GPU_LAYERS", "-1")
        self.models_dir = Path("models/llm")
        self.models_dir.mkdir(exist_ok=True)
        # LLM-Router initialisieren (Modellwahl)
        self.router = LLMRouter()

        self.available_models: Dict[str, Dict[str, Any]] = {
            "mistral": {
                "name": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
                "display_name": "Mistral 7B Nemo Instruct",
                "description": "Einsatzgebiet: Code, technische Details, Systembefehle, schnelle Antworten",
                "context_length": 8192,
                "parameters": "7B",
                "use_case": "code",
                "format": "gguf",
                "size_gb": 7.48,
                "repo_url": "https://huggingface.co/second-state/Mistral-Nemo-Instruct-2407-GGUF",
                "strengths": ["praezise", "strukturiert", "logisch", "schnell", "deutsch-freundlich", "code"],
                "weaknesses": ["weniger kreativ"],
                "role": "technical",
            },
            "deepseek": {
                "name": "deepseek-r1-distill-llama-8b-q4_k_m.gguf",
                "alt_names": [
                    "DeepSeek-R1-Distill-Llama-8B.Q4_K_M.gguf",
                    "DeepSeek-R1-Distill-Llama-8B.Q4_K_S.gguf",
                    "DeepSeek-R1-Distill-Llama-8B.Q5_K_M.gguf",
                    "deepseek-r1-distill-llama-8b.gguf"
                ],
                "display_name": "DeepSeek R1 Distill Llama 8B",
                "description": "Einsatzgebiet: Analysen, komplexe Daten, lange Texte, Reasoning",
                "context_length": 8192,
                "parameters": "8B",
                "use_case": "analysis",
                "format": "gguf",
                "size_gb": 6.9,
                "repo_url": "https://huggingface.co/Triangle104/DeepSeek-R1-Distill-Llama-8B-Q4_K_M-GGUF",
                "strengths": ["hohe rechenleistung", "genauigkeit", "analysen", "reasoning"],
                "weaknesses": ["groesser", "langsamer"],
                "role": "analysis",
            },
            "qwen": {
                "name": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
                "alt_names": [
                    "Qwen2.5-7B-Instruct-Q4_K_S.gguf",
                    "Qwen2.5-7B-Instruct-Q5_K_M.gguf",
                    "qwen2.5-7b-instruct-q4_k_m.gguf",
                ],
                "display_name": "Qwen 2.5 7B Instruct",
                "description": "Einsatzgebiet: Vielseitig, mehrsprachig, Balance zwischen Geschwindigkeit und Qualitaet",
                "context_length": 32768,
                "parameters": "7B",
                "use_case": "conversation",
                "format": "gguf",
                "size_gb": 5.2,
                "repo_url": "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF",
                "strengths": ["vielseitig", "mehrsprachig", "schnell", "balanciert"],
                "weaknesses": ["weniger spezialisiert"],
                "role": "balanced",
            },
            "llama": {
                "name": "llama-2-7b-chat.Q4_K_M.gguf",
                "alt_names": [
                    "llama-2-7b-chat.Q4_K_S.gguf",
                    "llama-2-7b-chat.Q5_K_M.gguf",
                    "Llama-2-7B-Chat-Q4_K_M.gguf",
                    "llama-2-7b.Q4_K_M.gguf",
                ],
                "display_name": "Llama 2 7B Chat",
                "description": "Einsatzgebiet: Unterhaltung, kreative Aufgaben, freundliche Responses",
                "context_length": 4096,
                "parameters": "7B",
                "use_case": "creative",
                "format": "gguf",
                "size_gb": 4.0,
                "repo_url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF",
                "strengths": ["kreativ", "freundlich", "konversationell", "kleine groesse"],
                "weaknesses": ["weniger praezise", "begrenzte technische faehigkeiten"],
                "role": "creative",
            },
        }

        self.default_model: Optional[str] = "mistral"

        self.current_model: Optional[str] = None
        self.model_instance: Optional[Any] = None
        self.model_loaded: bool = False
        self.use_gpu: bool = False
        self.model_lock = threading.RLock()

        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.model_usage_order: List[str] = []
        self.max_cached_models: int = int(os.environ.get("LLM_MAX_CACHED_MODELS", "2"))
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds: int = int(os.environ.get("LLM_CACHE_TTL", "300"))

        # Progress callback for downloads
        self._progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None

        self.use_case_keywords: Dict[str, List[str]] = {
            "code": ["code", "programm", "skript", "funktion", "bug", "regex", "algorithmus", "entwickle"],
            "creative": ["geschichte", "gedicht", "kreativ", "erfinde", "story", "lyrics", "idee"],
            "analysis": ["analyse", "bewerte", "vergleich", "daten", "statistik", "bericht", "zusammenfassung"],
            "emotion": ["gefuehl", "emotion", "motivieren", "troeste", "ermutige", "rat"],
            "conversation": ["hallo", "danke", "wie geht", "erzaehle", "plaudern", "hey"],
            "knowledge": ["wer ist", "was ist", "erklaere", "wissen", "fakten", "recherche"]
        }
        self.use_case_model_map: Dict[str, List[str]] = {
            "code": ["mistral", "deepseek", "qwen"],
            "analysis": ["deepseek", "mistral", "qwen"],
            "creative": ["llama", "mistral", "qwen"],
            "emotion": ["llama", "mistral", "qwen"],
            "conversation": ["qwen", "llama", "mistral"],
            "knowledge": ["deepseek", "qwen", "mistral"]
        }
        self.default_use_case: str = "conversation"
        self.logic_path_map: Dict[str, str] = {
            "automation": "code",
            "creative": "creative",
            "empathetic": "emotion",
            "support": "emotion",
            "analysis": "analysis",
            "research": "knowledge",
            "default": "conversation",
        }

        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history: int = 10
        # Etwas niedrigere Temperatur fuer praezisere, weniger ausschweifende Antworten
        self.default_temperature: float = 0.65
        self.default_max_tokens: int = 256
        self.logger.info("LLM-Manager initialisiert")
        self.auto_install_models()

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        return self.available_models

    @staticmethod
    def _format_bytes(value: Optional[int]) -> Optional[str]:
        if value is None or value < 0:
            return None
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} {units[-1]}"

    def get_model_overview(self) -> Dict[str, Dict[str, Any]]:
        """Gibt eine UI-fertige Übersicht aller bekannten Modelle zurück.

        - `downloaded`: ob eine lokale Modelldatei existiert
        - `ready`: ob das Modell in einem von llama.cpp unterstützten Format vorliegt
        - `local_path`: Pfad zur gefundenen Datei
        - `size_bytes` / `size_human`: tatsächliche Dateigröße (falls vorhanden)
        - `loaded`: ob das Modell aktuell im Speicher liegt
        - `active`: ob es das aktuell genutzte Modell ist
        - `metadata`: Laufzeitinfos (Load-Dauer, GPU-Layer, etc.), falls vorhanden
        """
        overview: Dict[str, Dict[str, Any]] = {}

        for key, info in self.available_models.items():
            # Basis-Infos aus available_models kopieren, damit nichts verändert wird
            details = dict(info)

            # lokale Datei suchen
            candidate_path: Optional[Path] = None
            size_bytes: Optional[int] = None

            for path in self._candidate_model_paths(key):
                if path.exists():
                    candidate_path = path
                    try:
                        size_bytes = path.stat().st_size
                    except OSError:
                        size_bytes = None
                    break

            # Status-Flags ergänzen
            details.update(
                {
                    "downloaded": bool(candidate_path),
                    "ready": self.is_model_ready(key),
                    "local_path": str(candidate_path) if candidate_path else None,
                    "size_bytes": size_bytes,
                    "size_human": self._format_bytes(size_bytes),
                    "loaded": key in self.loaded_models,
                    "active": bool(self.model_loaded and self.current_model == key),
                }
            )

            # Laufzeit-Metadaten, falls vorhanden
            metadata = self.model_metadata.get(key, {})
            if metadata:
                details["metadata"] = metadata

            overview[key] = details

        return overview

    def _resolve_startup_models(self) -> List[str]:
        if not self.settings:
            return []
        startup_models: List[str] = []
        preferred_order: List[str] = [
            model_key for model_key in ("mistral", "deepseek", "qwen", "llama") if model_key in self.available_models
        ]
        preferred_order.extend(
            model_key for model_key in self.available_models.keys() if model_key not in preferred_order
        )
        get_strategy = getattr(self.settings, "get_model_load_strategy", None)
        get_section = getattr(self.settings, "get_model_settings", None)
        fallback_section: Dict[str, Any] = {}
        if callable(get_section):
            try:
                section = get_sectio
