"""
LLM-Router für J.A.R.V.I.S.
Entscheidet, welches Sprachmodell für eine bestimmte Anfrage am besten geeignet ist.
"""

from typing import Dict, List, Optional, Any
import re
from pathlib import Path
import logging

class LLMRouter:
    """Verwaltet das Routing von Anfragen an die entsprechenden Sprachmodelle."""
    
    def __init__(self):
        self.logger = logging.getLogger("J.A.R.V.I.S.")
        self.logger.info("LLM-Router initialisiert")

        # Modell-Kompetenzen
        self.model_capabilities = {
            "llama3": {
                "strengths": ["dialog", "kreativ", "brainstorming"],
                "weaknesses": ["hard_tech", "praezise_code"],
                "max_tokens": 8192,
            },
            "mistral": {
                "strengths": ["code", "technik", "systembefehle", "logik"],
                "weaknesses": ["kreativ"],
                "max_tokens": 8192,
            },
            "deepseek": {
                "strengths": ["analyse", "daten", "reasoning", "planung"],
                "weaknesses": ["unterhaltung", "tempo"],
                "max_tokens": 8192,
            },
        }

        # Standard-Fallback-Modell
        self.default_model = "llama3"

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analysiert die Anfrage und extrahiert Merkmale fuer die Modellwahl."""
        original = query or ''
        text = original.lower()
        tokens = re.findall(r"\w+", text)
        token_set = set(tokens)

        technical_terms = {"code", "programm", "funktion", "klasse", "algorithmus", "script", "befehl", "technisch", "terminal"}
        creative_terms = {"schreibe", "erzahle", "geschichte", "gedicht", "idee", "brainstorm"}
        analysis_terms = {"analyse", "bewerte", "statistik", "daten", "bericht", "auswertung", "recherche", "strategie", "planung", "vergleich"}

        analysis = {
            "length": len(tokens),
            "has_question": any(symbol in text for symbol in ["wer", "was", "wo", "wann", "warum", "wie", "wieso", "weshalb", "?"]),
            "is_technical": any(term in token_set for term in technical_terms),
            "is_creative": any(term in token_set for term in creative_terms),
            "needs_analysis": any(term in token_set for term in analysis_terms),
            "tokens": token_set,
        }
        if analysis["length"] > 150:
            analysis["needs_analysis"] = True
        analysis["is_conversational"] = not analysis["is_technical"] and not analysis["needs_analysis"]
        return analysis

    def get_best_model(self, query: str, available_models: List[str]) -> str:
        """Bestimmt das beste verfuegbare Modell fuer die gegebene Anfrage."""
        if not available_models:
            return self.default_model

        # Normalisiere und mappe Modellnamen/Dateinamen auf bekannte Keys
        normalized = []
        for name in available_models:
            key = self._map_to_known_model(name)
            if key:
                normalized.append(key)
        # Falls nichts gemappt werden konnte, verwende Originale (defensiv)
        candidates = normalized or [m.lower() for m in available_models]

        if len(candidates) == 1:
            return candidates[0]

        analysis = self.analyze_query(query)
        model_scores: Dict[str, float] = {}

        for model in candidates:
            if model not in self.model_capabilities:
                continue
            score = 0.0
            if model == "llama3":
                if analysis["is_conversational"]:
                    score += 3
                if analysis["is_creative"]:
                    score += 2
                if analysis["is_technical"]:
                    score -= 1
                if analysis["needs_analysis"]:
                    score -= 1
            elif model == "mistral":
                if analysis["is_technical"]:
                    score += 3
                if analysis["has_question"] and analysis["is_technical"]:
                    score += 1
                if analysis["is_creative"] and not analysis["is_technical"]:
                    score -= 1
            elif model == "deepseek":
                if analysis["needs_analysis"]:
                    score += 3
                if analysis["length"] > 200:
                    score += 1
                if analysis["is_technical"] and not analysis["needs_analysis"]:
                    score -= 1
                if analysis["is_conversational"] and analysis["length"] < 60:
                    score -= 1
            model_scores[model] = score

        if not model_scores:
            return self.default_model

        # Top-Scores zur Nachvollziehbarkeit loggen
        sorted_scores = sorted(model_scores.items(), key=lambda item: item[1], reverse=True)
        best_model, best_score = sorted_scores[0]
        top_log = ", ".join([f"{m}:{s:.2f}" for m, s in sorted_scores[:3]])
        self.logger.info(
            "Modellauswahl: %s (Score %.2f) | Top: %s | Anfrage: %s",
            best_model,
            best_score,
            top_log,
            query[:60] if query else "",
        )
        return best_model

    def should_use_rag(self, query: str) -> bool:
        """Heuristik fuer RAG: nutze Wissensabruf bei Faktenfragen."""
        question_words = ["wer", "was", "wo", "wann", "warum", "wie", "erklaere", "bedeutet", "daten"]
        lowered = (query or "").lower()
        return any(word in lowered for word in question_words)
    
    def get_model_parameters(self, model_name: str) -> Dict:
        """Gibt die empfohlenen Parameter für ein bestimmtes Modell zurück."""
        if model_name not in self.model_capabilities:
            return {"temperature": 0.7, "max_tokens": 2000}
        
        params = {
            "temperature": 0.7,
            "max_tokens": self.model_capabilities[model_name].get("max_tokens", 2000)
        }
        
        # Anpassungen basierend auf dem Modelltyp
        if model_name == "llama3":
            params["top_p"] = 0.9
        elif model_name == "mistral":
            params["top_p"] = 0.95
            params["temperature"] = 0.8  # Etwas kreativer
        elif model_name == "deepseek":
            params["top_p"] = 0.85
            params["temperature"] = 0.65  # analytischer, konservativer
        
        return params

    # --- Hilfsfunktionen ---
    def _map_to_known_model(self, name: str) -> Optional[str]:
        if not name:
            return None
        lowered = name.strip().lower()
        # Direkte Treffer
        if lowered in self.model_capabilities:
            return lowered
        # Heuristische Aliase anhand von Substrings/Dateinamen
        if "llama" in lowered or "meta-llama" in lowered:
            return "llama3"
        if "mistral" in lowered or "nous-hermes" in lowered:
            return "mistral"
        if "deepseek" in lowered:
            return "deepseek"
        return None
