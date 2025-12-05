"""
JarvisCore Memory System

Dieses Modul verwaltet verschiedene Arten von Speicher:
- Short-term Memory: Kurzzeitgedächtnis für aktuelle Konversationen
- Long-term Memory: Langzeitgedächtnis für persistente Informationen
- Vector Memory: Vektorbasierter Speicher für semantische Suche
- Timeline Memory: Zeitbasierter Speicher für Events
"""

from .manager import MemoryManager
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .vector import VectorMemory
from .timeline import TimelineMemory

__all__ = [
    'MemoryManager',
    'ShortTermMemory',
    'LongTermMemory',
    'VectorMemory',
    'TimelineMemory',
]

__version__ = '1.0.0'
