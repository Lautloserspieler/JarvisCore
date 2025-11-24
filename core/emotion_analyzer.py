"""
Emotion analysis helper for Jarvis.

Provides a lightweight heuristic for classifying the general tone of incoming
audio snippets so that downstream components can adapt their responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import numpy as np


@dataclass
class EmotionResult:
    """Container for analysed emotion data."""

    label: str
    energy: float
    variance: float
    zero_crossing_rate: float
    confidence: float

    def as_dict(self) -> Dict[str, Union[float, str]]:
        return {
            "label": self.label,
            "energy": self.energy,
            "variance": self.variance,
            "zero_crossing_rate": self.zero_crossing_rate,
            "confidence": self.confidence,
        }


class EmotionAnalyzer:
    """Collects rolling audio metrics and derives a coarse emotion label."""

    def __init__(self) -> None:
        self._energy_samples: List[float] = []
        self._variance_samples: List[float] = []
        self._zcr_samples: List[float] = []
        self._update_count: int = 0
        self.reset()

    def reset(self) -> None:
        self._energy_samples.clear()
        self._variance_samples.clear()
        self._zcr_samples.clear()
        self._update_count = 0
        self._cached_result: Optional[EmotionResult] = None

    def update(self, audio_chunk: bytes) -> None:
        if not audio_chunk:
            return
        try:
            samples = np.frombuffer(audio_chunk, dtype=np.int16)
        except (ValueError, TypeError):
            return
        if samples.size == 0:
            return

        normalized = samples.astype(np.float32) / 32768.0
        energy = float(np.sqrt(np.mean(np.square(normalized))))
        variance = float(np.var(normalized))
        zcr = float(np.mean(np.diff(np.signbit(normalized)) != 0))

        self._energy_samples.append(energy)
        self._variance_samples.append(variance)
        self._zcr_samples.append(zcr)
        self._update_count += 1
        self._cached_result = None

    def _classify(self, energy: float, variance: float, zcr: float) -> EmotionResult:
        # Heuristic thresholds tuned for 16 kHz / int16 input.
        if energy < 0.01:
            label = "calm"
        elif energy < 0.025:
            label = "neutral"
        elif energy > 0.05 and variance > 0.0025:
            label = "excited"
        elif energy > 0.045 and variance < 0.0015:
            label = "focused"
        else:
            label = "expressive"

        if zcr < 0.08 and energy > 0.04:
            label = "confident"
        elif zcr > 0.18 and energy < 0.03:
            label = "uncertain"
        elif zcr > 0.22 and energy > 0.035:
            label = "happy"

        confidence = min(1.0, float(self._update_count) / 12.0)
        return EmotionResult(
            label=label,
            energy=energy,
            variance=variance,
            zero_crossing_rate=zcr,
            confidence=confidence,
        )

    def finalize(self) -> EmotionResult:
        if self._cached_result is not None:
            return self._cached_result
        if not self._energy_samples:
            result = EmotionResult("neutral", 0.0, 0.0, 0.0, 0.0)
            self._cached_result = result
            return result

        energy = float(np.mean(self._energy_samples))
        variance = float(np.mean(self._variance_samples))
        zcr = float(np.mean(self._zcr_samples))
        result = self._classify(energy, variance, zcr)
        self._cached_result = result
        return result

    def snapshot(self) -> EmotionResult:
        """Immediate read without resetting internal buffers."""
        return self.finalize()

