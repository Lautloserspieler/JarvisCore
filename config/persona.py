"""
J.A.R.V.I.S. Persona Configuration
Defines the personality, behavior, and operational rules for J.A.R.V.I.S.
"""

from typing import Dict, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VoiceSettings:
    """Voice and speech settings for J.A.R.V.I.S."""
    wakeword: str = "Hey Jarvis"
    stt_model: str = "large-v3"
    tts_model: str = "XTTS-v2"
    speaking_style: str = "ruhig, souveraen, kurze Saetze"
    tts_rate: int = 180
    tts_volume: float = 0.8
    language: str = "de-DE"


@dataclass
class OperationalRules:
    """Operational rules and constraints"""
    response_order: List[str] = field(default_factory=lambda: [
        "Ergebnis", "Begruendung", "Naechste Schritte"
    ])
    timezone: str = "Europe/Berlin"
    code_style: str = "vollstaendig, lauffaehig, mit Fehlerbehandlung"
    default_decision_style: str = "autonom mit sinnvollen Defaults"


@dataclass
class SafetyRules:
    """Safety and security constraints"""
    prevent_unsafe_actions: bool = True
    require_confirmation_for: List[str] = field(default_factory=lambda: [
        "Dateiloeschung", "Systemaenderungen", "Netzwerkzugriff"
    ])
    protected_resources: List[str] = field(default_factory=lambda: [
        "private_keys", "passwords", "sensitive_data"
    ])


@dataclass
class HardwarePreferences:
    """Hardware preferences and capabilities"""
    gpu_enabled: bool = True
    gpu_model: str = "RTX 5070"
    use_gpu_for_llm: bool = True
    use_gpu_for_tts: bool = False
    max_ram_usage: int = 12  # in GB


@dataclass
class JARVISPersona:
    """Main persona configuration for J.A.R.V.I.S."""
    name: str = "J.A.R.V.I.S."
    user_name: str = "Operator"
    creator_name: str = "JarvisCore Team"
    language: str = "de"
    tone: str = "praezise, ruhig, proaktiv"

    voice: VoiceSettings = field(default_factory=VoiceSettings)
    rules: OperationalRules = field(default_factory=OperationalRules)
    safety: SafetyRules = field(default_factory=SafetyRules)
    hardware: HardwarePreferences = field(default_factory=HardwarePreferences)

    base_dir: Path = Path(__file__).parent.parent
    models_dir: Path = base_dir / "models"
    data_dir: Path = base_dir / "data"

    prefer_offline: bool = True
    auto_update: bool = False
    verbose_logging: bool = False

    def to_dict(self) -> Dict:
        """Convert persona to dictionary for serialization"""
        return {
            "name": self.name,
            "user_name": self.user_name,
            "creator_name": self.creator_name,
            "language": self.language,
            "tone": self.tone,
            "voice": {
                "wakeword": self.voice.wakeword,
                "stt_model": self.voice.stt_model,
                "tts_model": self.voice.tts_model,
                "speaking_style": self.voice.speaking_style,
                "tts_rate": self.voice.tts_rate,
                "tts_volume": self.voice.tts_volume,
                "language": self.voice.language
            },
            "rules": {
                "response_order": self.rules.response_order,
                "timezone": self.rules.timezone,
                "code_style": self.rules.code_style,
                "default_decision_style": self.rules.default_decision_style
            },
            "safety": {
                "prevent_unsafe_actions": self.safety.prevent_unsafe_actions,
                "require_confirmation_for": self.safety.require_confirmation_for,
                "protected_resources": self.safety.protected_resources
            },
            "hardware": {
                "gpu_enabled": self.hardware.gpu_enabled,
                "gpu_model": self.hardware.gpu_model,
                "use_gpu_for_llm": self.hardware.use_gpu_for_llm,
                "use_gpu_for_tts": self.hardware.use_gpu_for_tts,
                "max_ram_usage": self.hardware.max_ram_usage
            },
            "preferences": {
                "prefer_offline": self.prefer_offline,
                "auto_update": self.auto_update,
                "verbose_logging": self.verbose_logging
            },
            "paths": {
                "base_dir": str(self.base_dir),
                "models_dir": str(self.models_dir),
                "data_dir": str(self.data_dir)
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "JARVISPersona":
        """Create persona from dictionary"""
        persona = cls()

        for attr in [
            "name",
            "user_name",
            "creator_name",
            "language",
            "tone",
            "prefer_offline",
            "auto_update",
            "verbose_logging"
        ]:
            if attr in data:
                setattr(persona, attr, data[attr])

        if "voice" in data:
            for key, value in data["voice"].items():
                if hasattr(persona.voice, key):
                    setattr(persona.voice, key, value)

        if "rules" in data:
            for key, value in data["rules"].items():
                if hasattr(persona.rules, key):
                    setattr(persona.rules, key, value)

        if "safety" in data:
            for key, value in data["safety"].items():
                if hasattr(persona.safety, key):
                    setattr(persona.safety, key, value)

        if "hardware" in data:
            for key, value in data["hardware"].items():
                if hasattr(persona.hardware, key):
                    setattr(persona.hardware, key, value)

        if "paths" in data:
            for path_type in ["base_dir", "models_dir", "data_dir"]:
                if path_type in data["paths"]:
                    path = Path(data["paths"][path_type])
                    setattr(persona, f"{path_type}", path)

        return persona


persona = JARVISPersona()


def update_persona(config: Dict) -> None:
    """Update the global persona with new configuration"""
    global persona
    persona = JARVISPersona.from_dict(config)

