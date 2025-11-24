"""
Simple voice biometrics helper for Jarvis.

Stores lightweight spectral fingerprints to authenticate a speaker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from utils.logger import Logger


class VoiceBiometricManager:
    """Manages enrollment and verification of simple voice signatures."""

    def __init__(self, storage_path: Optional[Path] = None, threshold: float = 0.88) -> None:
        self.logger = Logger()
        self.storage_path = Path(storage_path or "data/voice_profiles.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.threshold = float(threshold)
        self.profiles: Dict[str, Dict[str, float]] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.profiles = data
        except Exception as exc:
            self.logger.warning(f"Voice profile load failed: {exc}")

    def _save(self) -> None:
        try:
            self.storage_path.write_text(json.dumps(self.profiles, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.debug(f"Voice profile save failed: {exc}")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def verify(
        self,
        audio_blob: Optional[bytes],
        profile: str = "default",
        auto_enroll: bool = False,
    ) -> Tuple[bool, float]:
        if not audio_blob:
            return False, 0.0
        features = self._extract_features(audio_blob)
        if features is None:
            return False, 0.0
        profile_entry = self.profiles.get(profile)
        if not profile_entry:
            if auto_enroll:
                self.logger.info("Enrolling new voice profile '%s' via auto_enroll.", profile)
                self._enroll(profile, features)
                return True, 1.0
            self.logger.info(
                "Voice profile '%s' not found. Rejecting verification and prompting for enrollment.",
                profile,
            )
            return False, 0.0
        stored_vec = np.array(profile_entry.get("vector", []), dtype=np.float32)
        if stored_vec.size == 0:
            return False, 0.0
        score = float(np.dot(stored_vec, features) / (np.linalg.norm(stored_vec) * np.linalg.norm(features) + 1e-8))
        if score >= self.threshold:
            self._update_profile(profile, stored_vec, features)
            return True, score
        if auto_enroll and score >= (self.threshold * 0.85):
            self._update_profile(profile, stored_vec, features)
        return False, score

    def enroll_from_audio(self, audio_blob: Optional[bytes], profile: str = "default") -> bool:
        if not audio_blob:
            return False
        features = self._extract_features(audio_blob)
        if features is None:
            return False
        self._enroll(profile, features)
        return True

    def has_profile(self, profile: Optional[str] = None) -> bool:
        if not self.profiles:
            return False
        if profile:
            entry = self.profiles.get(profile)
            return bool(entry and entry.get("vector"))
        return any(entry.get("vector") for entry in self.profiles.values())

    def profile_count(self) -> int:
        return sum(1 for entry in self.profiles.values() if entry.get("vector"))

    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        overview: Dict[str, Dict[str, Any]] = {}
        for name, payload in self.profiles.items():
            if not isinstance(payload, dict):
                continue
            overview[name] = {
                "samples": int(payload.get("samples", 0)),
                "has_vector": bool(payload.get("vector")),
            }
        return overview

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _enroll(self, profile: str, feature_vec: np.ndarray) -> None:
        self.profiles[profile] = {
            "vector": feature_vec.astype(np.float32).tolist(),
            "samples": 1,
        }
        self._save()
        self.logger.info(f"Biometrisches Profil '{profile}' angelegt.")

    def _update_profile(self, profile: str, stored_vec: np.ndarray, new_vec: np.ndarray) -> None:
        entry = self.profiles.get(profile) or {}
        samples = int(entry.get("samples", 1))
        alpha = min(0.4, 1.0 / (samples + 1))
        updated = ((1.0 - alpha) * stored_vec) + (alpha * new_vec)
        updated = updated / (np.linalg.norm(updated) + 1e-8)
        self.profiles[profile] = {
            "vector": updated.astype(np.float32).tolist(),
            "samples": samples + 1,
        }
        self._save()

    def _extract_features(self, audio_blob: bytes) -> Optional[np.ndarray]:
        try:
            samples = np.frombuffer(audio_blob, dtype=np.int16).astype(np.float32)
        except Exception as exc:
            self.logger.debug(f"Audio konnte nicht verarbeitet werden: {exc}")
            return None
        if samples.size == 0:
            return None
        normalized = samples / 32768.0
        frame_size = 400
        hop_length = 160
        frames = []
        for start in range(0, normalized.size - frame_size + 1, hop_length):
            frame = normalized[start:start + frame_size]
            frames.append(frame * np.hanning(frame_size))
        if not frames:
            frames = [normalized]
        frames = np.stack(frames)
        energy = np.mean(np.square(frames), axis=1)
        zcr = np.mean(np.abs(np.diff(np.sign(frames), axis=1)), axis=1)
        spectrum = np.abs(np.fft.rfft(frames, axis=1))
        spectral_sum = np.sum(spectrum, axis=1) + 1e-8
        spectral_centroid = np.sum(
            (np.linspace(0.0, 1.0, spectrum.shape[1])[None, :]) * spectrum, axis=1
        ) / spectral_sum
        band_splits = np.array_split(np.arange(spectrum.shape[1]), 6)
        band_features = []
        for band in band_splits:
            if band.size == 0:
                band_features.append(0.0)
            else:
                band_features.append(float(np.mean(spectrum[:, band])))
        band_features = np.array(band_features, dtype=np.float32)
        feature = np.concatenate([
            [np.mean(energy), np.std(energy)],
            [np.mean(zcr), np.std(zcr)],
            [np.mean(spectral_centroid), np.std(spectral_centroid)],
            band_features,
        ])
        norm = np.linalg.norm(feature)
        if not np.isfinite(norm) or norm == 0.0:
            return None
        return (feature / norm).astype(np.float32)
