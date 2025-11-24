"""
Core package for J.A.R.V.I.S.
"""

# Exportiere wichtige Klassen
from .speech_recognition import SpeechRecognizer, SpeechRecognizerConfig
from .command_processor import CommandProcessor
from .knowledge_manager import KnowledgeManager
from .llm_manager import LLMManager
from .xtts_tts import XTTSTTS
from .long_term_memory import LongTermMemory
from .short_term_memory import ShortTermMemory
from .memory_manager import MemoryManager
from .clarification_module import ClarificationModule

__all__ = [
    'SpeechRecognizer',
    'SpeechRecognizerConfig',
    'CommandProcessor',
    'KnowledgeManager',
    'LLMManager',
    'XTTSTTS'
]
