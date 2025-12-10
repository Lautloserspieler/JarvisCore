"""
LLM-Manager fuer J.A.R.V.I.S.
Verwaltet lokale Sprachmodelle (Llama, Mistral, etc.)
"""

import os
import json
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
            "llama3": {
                "name": "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
                "display_name": "Meta Llama 3 8B Instruct",
                "description": "Einsatzgebiet: Kreative Antworten, offene Fragen, Dialoge",
                "context_length": 8192,
                "parameters": "8B",
                "use_case": "conversation",
                "format": "gguf",
                "size_gb": 4.9,
                "repo_url": "https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct-GGUF",
                "strengths": ["flexibel", "generativ", "ideenreich"],
                "weaknesses": ["weniger praezise bei Code oder Technik"],
                "role": "standard",
            },
            "mistral": {
                "name": "Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf",
                "display_name": "Nous Hermes 2 (Mistral 7B DPO)",
                "description": "Einsatzgebiet: Code, technische Details, Systembefehle",
                "context_length": 8192,
                "parameters": "7B",
                "use_case": "code",
                "format": "gguf",
                "size_gb": 4.1,
                "repo_url": "https://huggingface.co/NousResearch/Nous-Hermes-2-Mistral-7B-DPO-GGUF",
                "strengths": ["praezise", "strukturiert", "logisch"],
                "weaknesses": ["weniger kreativ"],
                "role": "technical",
            },
            "deepseek": {
                "name": "DeepSeek-R1-8B-f16.gguf",
                "alt_names": [
                    "DeepSeek-R1-Distill-Llama-8B.Q4_K_M.gguf",
                    "DeepSeek-R1-Distill-Llama-8B.Q4_K_S.gguf",
                    "DeepSeek-R1-Distill-Llama-8B.Q5_K_M.gguf",
                    "DeepSeek-R1-Distill-Llama-8B.gguf"
                ],
                "display_name": "DeepSeek R1 Distill Llama 8B",
                "description": "Einsatzgebiet: Analysen, komplexe Daten, lange Texte",
                "context_length": 8192,
                "parameters": "8B",
                "use_case": "analysis",
                "format": "safetensors",
                "size_gb": 6.9,
                "repo_url": "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
                "strengths": ["hohe rechenleistung", "genauigkeit"],
                "weaknesses": ["groesser", "langsamer", "nur bei bedarf aktiv"],
                "role": "analysis",
            },
        }

        self.default_model: Optional[str] = next(iter(self.available_models.keys()), None)


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

        self.use_case_keywords: Dict[str, List[str]] = {
            "code": ["code", "programm", "skript", "funktion", "bug", "regex", "algorithmus", "entwickle"],
            "creative": ["geschichte", "gedicht", "kreativ", "erfinde", "story", "lyrics", "idee"],
            "analysis": ["analyse", "bewerte", "vergleich", "daten", "statistik", "bericht", "zusammenfassung"],
            "emotion": ["gefuehl", "emotion", "motivieren", "troeste", "ermutige", "rat"],
            "conversation": ["hallo", "danke", "wie geht", "erzaehle", "plaudern", "hey"],
            "knowledge": ["wer ist", "was ist", "erklaere", "wissen", "fakten", "recherche"]
        }
        self.use_case_model_map: Dict[str, List[str]] = {
            "code": ["mistral", "llama3"],
            "analysis": ["deepseek", "llama3", "mistral"],
            "creative": ["llama3", "mistral"],
            "emotion": ["llama3", "mistral"],
            "conversation": ["llama3", "mistral"],
            "knowledge": ["deepseek", "llama3", "mistral"]
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
        overview: Dict[str, Dict[str, Any]] = {}
        for key, info in self.available_models.items():
            details = dict(info)
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
            model_key for model_key in ("llama3", "mistral", "deepseek") if model_key in self.available_models
        ]
        preferred_order.extend(
            model_key for model_key in self.available_models.keys() if model_key not in preferred_order
        )
        get_strategy = getattr(self.settings, "get_model_load_strategy", None)
        get_section = getattr(self.settings, "get_model_settings", None)
        fallback_section: Dict[str, Any] = {}
        if callable(get_section):
            try:
                section = get_section("llm")
                if isinstance(section, dict):
                    fallback_section = section
            except Exception:
                fallback_section = {}
        for model_key in preferred_order:
            strategy = None
            if callable(get_strategy):
                try:
                    strategy = get_strategy(model_key, default="on_demand", model_type="llm")
                except Exception:
                    strategy = None
            if strategy not in ("startup", "on_demand") and fallback_section:
                entry = fallback_section.get(model_key)
                if isinstance(entry, dict):
                    strategy = entry.get("load_strategy")
            if strategy == "startup" and model_key not in startup_models:
                startup_models.append(model_key)
        return startup_models

    def _candidate_model_paths(self, model_key: str) -> List[Path]:
        info = self.available_models.get(model_key)
        if not info:
            return []
        names: List[str] = []
        primary = info.get("name")
        if primary:
            names.append(primary)
            base = Path(primary)
            stem = base.stem
            suffix = base.suffix.lower() if base.suffix else ''
            if suffix == '.safetensors':
                names.extend([
                    f"{stem}.gguf",
                    f"{stem}.Q4_K_M.gguf",
                    f"{stem}.Q4_K_S.gguf",
                    f"{stem}.Q5_K_M.gguf",
                ])
        for alias in info.get("alt_names", []):
            if alias:
                names.append(alias)
        seen: Set[str] = set()
        candidates: List[Path] = []
        for name in names:
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(self.models_dir / name)
        return candidates

    def check_model_exists(self, model_key: str) -> bool:
        if model_key not in self.available_models:
            return False
        return any(path.exists() for path in self._candidate_model_paths(model_key))

    def is_model_ready(self, model_key: str) -> bool:
        if model_key not in self.available_models:
            return False
        for path in self._candidate_model_paths(model_key):
            if path.exists() and self._is_supported_model_file(path):
                return True
        return False

    def choose_model_for_prompt(
        self,
        prompt: str,
        use_case: Optional[str] = None,
        task_hint: Optional[str] = None,
    ) -> str:
        resolved_use_case = use_case or self.classify_use_case(prompt)
        if task_hint:
            mapped = self.logic_path_map.get(task_hint.lower())
            if mapped:
                resolved_use_case = mapped
        candidate_models = self.use_case_model_map.get(resolved_use_case, [])
        for candidate in candidate_models:
            if self.is_model_ready(candidate):
                return candidate

        # Router-gestuetzte Auswahl unter allen verfügbaren/geladenen Modellen
        try:
            ready_models = [key for key in self.available_models if self.is_model_ready(key)]
            if hasattr(self, "router") and ready_models:
                chosen = self.router.get_best_model(prompt, ready_models)
                if chosen in ready_models:
                    return chosen
        except Exception as _router_exc:  # defensiv: Router darf nicht brechen
            self.logger.debug(f"LLMRouter Auswahl uebersprungen: {_router_exc}")

        # Fallbacks, falls keine Zuordnung moeglich ist
        for fallback_use_case in ("conversation", "analysis", "code", "knowledge"):
            for candidate in self.use_case_model_map.get(fallback_use_case, []):
                if self.is_model_ready(candidate):
                    return candidate

        for key in self.available_models:
            if self.is_model_ready(key):
                return key
        return self.default_model

    def _score_use_case(self, prompt: str) -> Dict[str, int]:
        text = prompt.lower()
        scores = {key: 0 for key in self.use_case_keywords}

        for category, keywords in self.use_case_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    scores[category] += 2 if f' {keyword} ' in f' {text} ' else 1

        if len(text) > 200:
            scores["analysis"] += 1
        if '?' in prompt:
            scores["analysis"] += 1
        if any(token in text for token in ["hilfe", "chatte", "unterhalte"]):
            scores["conversation"] += 1
        if any(token in text for token in ["erzaehle", "fantasie", "erschaffe", "rolle"]):
            scores["creative"] += 1
        if any(token in text for token in ["troest", "angst", "freue", "gluecklich", "traurig"]):
            scores["emotion"] += 2
        if any(token in text for token in ["recherche", "datenblatt", "forschung", "quelle"]):
            scores["knowledge"] += 2
        return scores

    def classify_use_case(self, prompt: str) -> str:
        scores = self._score_use_case(prompt)
        best_category = max(scores, key=lambda key: scores[key])
        return best_category if scores.get(best_category, 0) > 0 else self.default_use_case

    def predict_use_case(self, prompt: str) -> Dict[str, Any]:
        scores = self._score_use_case(prompt)
        best_category = max(scores, key=lambda key: scores[key])
        return {
            "use_case": best_category if scores.get(best_category, 0) > 0 else self.default_use_case,
            "scores": scores,
        }


    def _gpu_preferred(self) -> bool:
        prefer_env = os.environ.get("LLAMA_USE_GPU", "0").lower() in {"1", "true", "yes"}
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
        cuda_enabled = cuda_visible not in (None, "", "-1")
        return prefer_env or cuda_enabled

    def _preferred_gpu_layers(self) -> Optional[int]:
        """Read desired GPU layer setting from env if provided.

        Returns an int (e.g. -1 for full offload) or None if not specified.
        """
        raw = os.environ.get("LLAMA_GPU_LAYERS")
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _gpu_layer_candidates(self) -> List[int]:
        if not self._gpu_preferred() or Llama is None:
            return [0]
        preferred = self._preferred_gpu_layers()
        if preferred is not None:
            return [preferred, 0]
        return [-1, 0]

    def _is_supported_model_file(self, model_path: Path) -> bool:
        return model_path.suffix.lower() in {".gguf", ".bin", ".ggml"}


    def load_model(self, model_key: str = "mistral") -> bool:
        with self.model_lock:
            if model_key not in self.available_models:
                self.logger.error(f"Unbekanntes Modell: {model_key}")
                return False

            if model_key in self.loaded_models:
                metadata = self.model_metadata.get(model_key, {})
                self.logger.debug("Modell bereits im Cache: %s", model_key)
                self.current_model = model_key
                self.model_instance = self.loaded_models[model_key]
                self.model_loaded = True
                self.use_gpu = bool(metadata.get("gpu_layers", 0))
                self._mark_model_used(model_key)
                return True

            model_info = self.available_models[model_key]
            candidate_paths = self._candidate_model_paths(model_key)

            if not candidate_paths:
                self.logger.warning(
                    "Keine Modelldateien fuer %s gefunden. Erwartet wird: %s",
                    model_key,
                    model_info.get("name"),
                )
                return False

            model_path = None
            for candidate in candidate_paths:
                if candidate.exists() and self._is_supported_model_file(candidate):
                    model_path = candidate
                    break

            if model_path is None:
                for candidate in candidate_paths:
                    if candidate.exists():
                        model_path = candidate
                        break

            if model_path is None:
                self.logger.warning(
                    "Modell %s nicht gefunden. Bitte Datei %s in %s ablegen.",
                    model_key,
                    model_info.get("name"),
                    self.models_dir,
                )
                return False

            if not self._is_supported_model_file(model_path):
                self.logger.error(
                    "Modellformat %s wird aktuell nicht unterstuetzt. Bitte konvertieren Sie die Datei in das GGUF-Format (z.B. ueber convert-hf-to-gguf) und legen Sie sie erneut in %s ab.",
                    model_path.suffix,
                    self.models_dir,
                )
                return False

            if Llama is None:
                self.logger.warning("llama_cpp konnte nicht importiert werden. Verwende Fallback-Antworten.")
                self.current_model = model_key
                self.model_instance = None
                self.model_loaded = False
                self.use_gpu = False
                self.conversation_history = []
                return False

            context_len = int(model_info.get("context_length", 2048))
            threads_env = os.environ.get("LLM_CPU_THREADS")
            threads = int(threads_env) if threads_env and threads_env.isdigit() else max(1, os.cpu_count() or 1)
            last_error: Optional[Exception] = None
            instance = None
            gpu_layers_used = 0
            load_start = time.time()

            for gpu_layers in self._gpu_layer_candidates():
                try:
                    self.logger.info(
                        "Modell wird geladen: %s (GPU-Layer: %s, Kontext: %s, Threads: %s)"
                        % (model_info["name"], gpu_layers, context_len, threads)
                    )
                    instance = Llama(
                        model_path=str(model_path),
                        n_ctx=context_len,
                        n_threads=threads,
                        n_gpu_layers=gpu_layers,
                        verbose=False,
                    )
                    gpu_layers_used = gpu_layers
                    break
                except Exception as err:  # pragma: no cover
                    last_error = err
                    self.logger.warning(
                        "Konnte Modell nicht mit GPU-Layer=%s laden: %s", gpu_layers, err
                    )
            if instance is None:
                self.logger.error(f"Fehler beim Laden des Modells: {last_error}")
                return False

            load_duration = time.time() - load_start

            self.loaded_models[model_key] = instance
            self.model_metadata[model_key] = {
                "loaded_at": time.time(),
                "last_used": time.time(),
                "gpu_layers": gpu_layers_used,
                "context_length": context_len,
                "load_duration": load_duration,
            }
            self._mark_model_used(model_key)
            self._evict_models_if_needed(exclude=model_key)

            self.current_model = model_key
            self.model_instance = instance
            self.model_loaded = True
            self.use_gpu = gpu_layers_used not in (None, 0)
            self.conversation_history = []

            self.logger.info(
                "Modell erfolgreich geladen: %s (GPU-Layer: %s, Kontext: %s, Threads: %s)",
                model_info["name"],
                gpu_layers_used,
                context_len,
                threads,
            )
            return True

    def _mark_model_used(self, model_key: str) -> None:
        if model_key in self.model_usage_order:
            self.model_usage_order.remove(model_key)
        self.model_usage_order.append(model_key)
        if model_key in self.model_metadata:
            self.model_metadata[model_key]["last_used"] = time.time()

    def _evict_models_if_needed(self, exclude: Optional[str] = None) -> None:
        while len(self.loaded_models) > self.max_cached_models:
            if not self.model_usage_order:
                break
            candidate = self.model_usage_order[0]
            if candidate == exclude and len(self.model_usage_order) > 1:
                self.model_usage_order.append(self.model_usage_order.pop(0))
                candidate = self.model_usage_order[0]
                if candidate == exclude:
                    break
            self._unload_model(candidate)

    def _unload_model(self, model_key: str) -> None:
        instance = self.loaded_models.pop(model_key, None)
        self.model_metadata.pop(model_key, None)
        if model_key in self.model_usage_order:
            self.model_usage_order.remove(model_key)
        if model_key == self.current_model:
            self.current_model = None
            self.model_instance = None
            self.model_loaded = False
            self.use_gpu = False
        try:
            del instance
        except Exception:  # pragma: no cover - defensive cleanup
            pass

    def _build_cache_key(self, model_key: str, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> str:
        payload = f"{model_key}|{system_prompt or ''}|{temperature}|{max_tokens}|{prompt}"
        digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        return f"{model_key}:{digest}"

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        cached = self.response_cache.get(cache_key)
        if not cached:
            return None
        if time.time() - cached.get('timestamp', 0) > self.cache_ttl_seconds:
            self.response_cache.pop(cache_key, None)
            return None
        return cached.get('response')

    def _store_cache(self, cache_key: str, response: str) -> None:
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
        }
        self._prune_cache()

    def _prune_cache(self) -> None:
        if len(self.response_cache) <= 128:
            return
        sorted_items = sorted(self.response_cache.items(), key=lambda item: item[1].get('timestamp', 0), reverse=True)
        for key, _ in sorted_items[128:]:
            self.response_cache.pop(key, None)


    def unload_model(self) -> None:
        with self.model_lock:
            if self.model_instance:
                self.model_instance = None
            self.current_model = None
            self.model_loaded = False
            self.use_gpu = False
            self.conversation_history = []
            self.logger.info("Modell entladen")

    def _ensure_model(self, model_key: str) -> bool:
        if not self.model_loaded or self.current_model != model_key:
            return self.load_model(model_key)
        return True

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_key: Optional[str] = None,
        use_case: Optional[str] = None,
        task_hint: Optional[str] = None,
        enable_cache: bool = True,
    ) -> Optional[str]:
        if temperature is None:
            temperature = self.default_temperature
        if max_tokens is None:
            max_tokens = self.default_max_tokens

        target_model = model_key or self.choose_model_for_prompt(prompt, use_case, task_hint)
        if not target_model:
            return self._return_fallback(prompt)

        if not self._ensure_model(target_model):
            return self._return_fallback(prompt)

        cache_key = None
        if enable_cache:
            cache_key = self._build_cache_key(target_model, prompt, system_prompt, temperature, max_tokens)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self.logger.debug("LLM Cache-Treffer fuer %s", target_model)
                self._add_to_history("user", prompt)
                self._add_to_history("assistant", cached_response)
                return cached_response

        with self.model_lock:
            model = self.loaded_models.get(target_model)
            if not model:
                return self._return_fallback(prompt)

            messages = self._build_chat_messages(prompt, system_prompt)
            try:
                result = model.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.9,
                )
                generated_text = result["choices"][0]["message"]["content"].strip()
            except Exception:
                context = self._build_context(prompt, system_prompt)
                result = model.create_completion(
                    prompt=context,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["Human:", "Assistant:"],
                )
                generated_text = result["choices"][0]["text"].strip()

        if not generated_text:
            return self._return_fallback(prompt)

        self._mark_model_used(target_model)
        self._add_to_history("user", prompt)
        self._add_to_history("assistant", generated_text)
        if cache_key:
            self._store_cache(cache_key, generated_text)
        return generated_text


    def _build_chat_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        system_message = system_prompt or (
            "Du bist J.A.R.V.I.S., ein deutscher KI-Assistent. Antworte kompakt (1–2 Saetze), ergebnisorientiert und sachlich. "
            "Keine ausgeschmueckten Hoefflichkeitsfloskeln, keine erfundenen Erinnerungen. "
            "Nenne direkt die Loesung oder den naechsten sinnvollen Schritt. "
            "Wenn mehrere Optionen bestehen, liste kurz die beste Option zuerst. "
            "Sprich immer Deutsch."
        )
        messages.append({"role": "system", "content": system_message})
        for entry in self.conversation_history[-self.max_history:]:
            role = "assistant" if entry.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": entry.get("content", "")})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _build_context(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        context_parts: List[str] = []
        if system_prompt:
            context_parts.append(f"System: {system_prompt}")
        else:
            context_parts.append(
                "System: Du bist J.A.R.V.I.S., ein deutscher KI-Assistent. "
                "Antworten kompakt (1–2 Saetze), ergebnisorientiert, keine erfundenen Erinnerungen."
            )
        for entry in self.conversation_history[-self.max_history:]:
            role = "Human" if entry["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {entry['content']}")
        context_parts.append(f"Human: {prompt}")
        context_parts.append("Assistant:")
        return "\n".join(context_parts)

    def _add_to_history(self, role: str, content: str) -> None:
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def _return_fallback(self, prompt: str) -> str:
        response = self._fallback_response(prompt)
        self._add_to_history("user", prompt)
        self._add_to_history("assistant", response)
        return response

    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        now = datetime.now()
        hour = now.hour
        greeting = "Guten Abend" if hour >= 18 or hour < 5 else ("Guten Morgen" if hour < 12 else "Guten Tag")

        if any(phrase in prompt_lower for phrase in ["wie geht", "wie laeuft", "wie ist dir", "alles gut"]):
            mood = random.choice([
                "Mir geht es gut und ich bin startklar. Was brauchen Sie?",
                "Alles im Lot – legen wir los. Wobei soll ich helfen?",
                "Passt, danke. Nennen Sie mir kurz das Ziel.",
            ])
            return f"{greeting}! {mood}"

        if any(phrase in prompt_lower for phrase in ["was kannst", "was machst", "was bist du"]):
            return (
                "Ich bin J.A.R.V.I.S., ein deutscher KI-Assistent. Ich kann Programme starten, Informationen zusammentragen,"
                " Technikfragen beantworten und kurze To-Dos planen. Sagen Sie mir kurz, was Sie brauchen."
            )

        if any(phrase in prompt_lower for phrase in ["danke", "dankeschon", "merci"]):
            return random.choice([
                "Sehr gern geschehen!",
                "Jederzeit gern - was steht als naechstes an?",
                "Freut mich, wenn ich helfen konnte.",
            ])

        if any(phrase in prompt_lower for phrase in ["tschuss", "auf wiedersehen", "bis spaeter", "mach es gut"]):
            return random.choice([
                "Auf Wiedersehen! Ich bin hier, wenn Sie mich brauchen.",
                "Bis zum naechsten Mal - bleiben Sie inspiriert!",
                "Gern wieder, einen schoenen Tag noch!",
            ])

        if any(word in prompt_lower for word in ["was ist", "wer ist", "erklaere", "erzaehl"]):
            return (
                "Das klingt spannend. Beschreiben Sie mir gern genauer, welche Aspekte Sie interessieren, dann suche ich "
                "gezielte Informationen fuer Sie heraus."
            )

        if any(term in prompt_lower for term in ["witz", "joke", "lustig"]):
            jokes = [
                "Warum konnte der Programmierer keine Pause machen? Weil er in einer Endlosschleife festhing!",
                "Wie nennt man eine KI, die immer Recht hat? Einen Wahrheitsalgorithmus.",
                "Ich wollte einen Witz ueber Strom erzaehlen, aber der wuerde Ihnen vielleicht zu sehr unter die Haut gehen.",
            ]
            return random.choice(jokes)

        if "wetter" in prompt_lower:
            return (
                "Ich kann lokale Wetterdaten nicht direkt abrufen, aber ich empfehle einen Blick in Ihre Wetter-App."
                " Falls Sie moechten, erinnere ich Sie gern daran, einen Regenschirm mitzunehmen."
            )

        templates = [
            "{greeting}! Erzaehlen Sie mir gern mehr darueber, was Sie beschaeftigt, dann schauen wir gemeinsam nach einer Loesung.",
            "Das klingt interessant. Welche Details sind fuer Sie am wichtigsten?",
            "Ich hoere zu - beschreiben Sie mir gern ein wenig genauer, wobei ich Sie unterstuetzen kann.",
            "Lassen Sie uns Schritt fuer Schritt vorgehen: Was waere der erste Punkt, den wir klaeren sollten?",
        ]
        return random.choice(templates).format(greeting=greeting)

    def get_model_status(self) -> Dict[str, Any]:
        return {
            "current_model": self.current_model,
            "model_loaded": bool(self.model_instance) and self.model_loaded,
            "available_models": list(self.available_models.keys()),
            "ready_models": [key for key in self.available_models if self.is_model_ready(key)],
            "conversation_length": len(self.conversation_history),
            "models_directory": str(self.models_dir),
            "use_gpu": self.use_gpu,
            "cached_models": list(self.loaded_models.keys()),
            "max_cached_models": self.max_cached_models,
            "response_cache_entries": len(self.response_cache),
        }

    def clear_history(self) -> None:
        self.conversation_history = []
        self.logger.info("Conversation History geleert")

    def set_system_prompt(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self.logger.info("System-Prompt gesetzt")

    def suggest_model_for_task(self, task_type: str) -> str:
        if task_type in ["programming", "technical", "system", "code"] and self.is_model_ready("mistral"):
            return "mistral"
        if task_type in ["analysis", "complex_reasoning", "research", "facts"] and self.is_model_ready("deepseek"):
            return "deepseek"
        if task_type in ["conversation", "creative_writing", "chat", "standard"] and self.is_model_ready("llama3"):
            return "llama3"
        return self.choose_model_for_prompt(task_type)

    def download_model_info(self, model_key: str) -> Dict[str, str]:
        info = self.available_models.get(model_key)
        if not info:
            return {}
        size = info.get("size_gb")
        if isinstance(size, (int, float)):
            size_str = f"{size:.1f}"
        elif size:
            size_str = str(size)
        else:
            size_str = "5.0"
        return {
            "url": info.get("repo_url", "https://huggingface.co/"),
            "filename": info.get("name"),
            "size_gb": size_str,
        }

    def _resolve_download_url(self, info: Dict[str, Any]) -> Optional[str]:
        explicit = info.get("download_url")
        if explicit:
            return explicit
        repo = info.get("repo_url")
        filename = info.get("name")
        if not repo or not filename:
            return None
        repo = str(repo).rstrip("/")
        filename = str(filename).lstrip("/")
        if repo.endswith(filename):
            return repo
        return f"{repo}/resolve/main/{filename}"

    def auto_install_models(self) -> None:
        try:
            self.logger.info("Pruefe verfuegbare LLM-Modelle...")
            configured_startup = self._resolve_startup_models()
            stop_after_first = False
            if configured_startup:
                target_models = [key for key in configured_startup if key in self.available_models]
            else:
                target_models = [key for key in ("llama3", "mistral", "deepseek") if key in self.available_models]
                stop_after_first = True
            if not target_models:
                self.logger.info("Keine LLM-Modelle zum automatischen Laden konfiguriert oder verfuegbar.")
                return
            loaded_any = False
            for model_key in target_models:
                if not self.check_model_exists(model_key):
                    self.logger.warning(
                        "Modell %s fehlt. Bitte Datei %s in %s ablegen.",
                        model_key,
                        self.available_models[model_key]["name"],
                        self.models_dir,
                    )
                    continue
                if model_key == "deepseek":
                    if not self.is_model_ready(model_key):
                        self.logger.info(
                            "Modell %s erkannt. Dieses Format setzt eine GGUF-Konvertierung voraus, bevor es mit llama.cpp geladen werden kann.",
                            model_key,
                        )
                        continue
                if self.load_model(model_key):
                    loaded_any = True
                    if stop_after_first:
                        break
            if configured_startup and not loaded_any:
                self.logger.info("Keine der konfigurierten Start-Modelle konnte geladen werden.")
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"Fehler bei automatischer Modell-Installation: {exc}")

    def download_model(self, model_key: str, progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None) -> bool:
        if requests is None:  # pragma: no cover - fallback, sollte praktisch nicht passieren
            raise RuntimeError("Das Paket 'requests' ist nicht installiert und wird fuer den Download benoetigt.")
        info = self.available_models.get(model_key)
        if not info:
            raise ValueError(f"Unbekanntes Modell: {model_key}")

        filename = info.get("name") or f"{model_key}.gguf"
        target_path = self.models_dir / filename
        if target_path.exists():
            self.logger.info("Modell bereits vorhanden: %s", target_path)
            if progress_cb:
                try:
                    size = target_path.stat().st_size
                except OSError:
                    size = 0
                progress_cb(
                    {
                        "model": model_key,
                        "status": "already_exists",
                        "downloaded": size,
                        "total": size,
                        "percent": 100,
                    }
                )
            return True

        url = self._resolve_download_url(info)
        if not url:
            raise RuntimeError("Download-URL konnte nicht bestimmt werden.")

        tmp_path = target_path.with_suffix(target_path.suffix + ".download")
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        # Get HuggingFace token from settings
        headers = {}
        if self.settings:
            try:
                llm_config = self.settings.get('llm', {})
                if isinstance(llm_config, dict):
                    token = llm_config.get('huggingface_token')
                    if token and isinstance(token, str) and token.strip():
                        headers['Authorization'] = f"Bearer {token.strip()}"
                        self.logger.info("Using HuggingFace token for download")
            except Exception as exc:
                self.logger.debug(f"Could not retrieve HuggingFace token: {exc}")

        self.logger.info("Starte Download fuer %s (%s)", model_key, url)
        downloaded = 0
        total = 0
        start_time = time.time()
        last_emit = 0.0

        def emit_progress(force: bool = False, status: str = "in_progress", message: Optional[str] = None) -> None:
            if not progress_cb:
                return
            now = time.time()
            nonlocal last_emit
            if not force and (now - last_emit) < 0.5:
                return
            percent = None
            if total:
                percent = (downloaded / total) * 100
            speed = None
            eta = None
            elapsed = max(now - start_time, 1e-3)
            if elapsed > 0:
                speed = downloaded / elapsed
                if total and downloaded < total and speed > 0:
                    eta = (total - downloaded) / speed
            payload = {
                "model": model_key,
                "status": status,
                "downloaded": downloaded,
                "total": total,
                "percent": percent,
                "speed": speed,
                "eta": eta,
            }
            if message:
                payload["message"] = message
            progress_cb(payload)
            last_emit = now

        response = None
        try:
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", "0")) or 0
            chunk_size = 4 * 1024 * 1024  # 4 MB
            emit_progress(force=True)
            with open(tmp_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    emit_progress()
            if not total:
                total = downloaded
            os.replace(tmp_path, target_path)
            self.logger.info("Modell heruntergeladen: %s", target_path)
            emit_progress(force=True)
            return True
        except Exception as exc:
            self.logger.error("Download fuer %s fehlgeschlagen: %s", model_key, exc)
            with contextlib.suppress(Exception):
                if tmp_path.exists():
                    tmp_path.unlink()
            raise
        finally:
            if response is not None:
                response.close()

    def get_available_disk_space(self) -> float:
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.models_dir)
            return free / (1024 ** 3)
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"Fehler beim Ermitteln des Festplattenspeichers: {exc}")
            return 0.0

    def check_model_requirements(self, model_key: str) -> Dict[str, Any]:
        try:
            import psutil
            download_info = self.download_model_info(model_key)
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            disk_gb = self.get_available_disk_space()
            required_ram = 8.0
            size_val = download_info.get("size_gb", "5.0")
            try:
                required_disk = float(size_val)
            except (TypeError, ValueError):
                required_disk = 5.0
            return {
                "sufficient_ram": ram_gb >= required_ram,
                "sufficient_disk": disk_gb >= required_disk,
                "model_available": model_key in self.available_models,
                "ram_gb": ram_gb,
                "disk_gb": disk_gb,
                "required_ram_gb": required_ram,
                "required_disk_gb": required_disk,
            }
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"Fehler bei Anforderungspruefung: {exc}")
            return {"sufficient_ram": False, "sufficient_disk": False, "model_available": False}
