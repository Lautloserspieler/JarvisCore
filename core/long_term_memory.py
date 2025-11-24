"""
Langzeitgedächtnis-System für J.A.R.V.I.S.
Speichert und verwaltet Informationen über längere Zeiträume.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class LongTermMemory:
    """Verwaltet das Langzeitgedächtnis des KI-Assistenten."""
    
    def __init__(self, storage_file: str = "data/memory.json"):
        """Initialisiert das Langzeitgedächtnis.
        
        Args:
            storage_file: Pfad zur Speicherdatei für das Gedächtnis
        """
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(storage_file) or '.', exist_ok=True)
        self.storage_file = storage_file
        self.memories: Dict[str, Dict[str, Any]] = {}
        self._load_memories()
    
    def _load_memories(self) -> None:
        """Lädt gespeicherte Erinnerungen aus der Datei."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.memories = json.load(f)
                logger.info(f"{len(self.memories)} Erinnerungen aus {self.storage_file} geladen")
            else:
                self.memories = {}
                logger.info("Keine vorhandenen Erinnerungen gefunden, neues Gedächtnis erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Erinnerungen: {e}")
            self.memories = {}
    
    def _save_memories(self) -> None:
        """Speichert die Erinnerungen in die Datei."""
        try:
            os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Erinnerungen: {e}")
    
    def remember(self, key: str, value: Any, category: str = "general", 
                expires: Optional[datetime] = None, importance: int = 5,
                topics: Optional[List[str]] = None, source: str = "user") -> bool:
        """Speichert eine Information im Langzeitgedächtnis.
        
        Args:
            key: Eindeutiger Schlüssel für die Information
            value: Zu speichernder Wert (muss JSON-serialisierbar sein)
            category: Kategorie für die Organisation (z.B. 'projekt', 'erinnerung', 'alltag')
            expires: Optionales Ablaufdatum
            importance: Wichtigkeit der Information (1-10)
            topics: Liste von Themen, die mit dieser Erinnerung verknüpft sind
            source: Quelle der Information ('user', 'system', 'conversation')
            
        Returns:
            True bei Erfolg, sonst False
        """
        try:
            memory_id = hashlib.md5(key.encode('utf-8')).hexdigest()
            now = datetime.now().isoformat()
            
            # Wenn die Erinnerung bereits existiert, aktualisieren
            if memory_id in self.memories:
                self.memories[memory_id].update({
                    'value': value,
                    'category': category,
                    'last_accessed': now,
                    'access_count': self.memories[memory_id].get('access_count', 0) + 1,
                    'importance': min(max(1, importance), 10),
                    'expires': expires.isoformat() if expires else None,
                    'topics': list(set(self.memories[memory_id].get('topics', []) + (topics or []))),
                    'source': source
                })
            else:
                # Neue Erinnerung erstellen
                self.memories[memory_id] = {
                    'key': key,
                    'value': value,
                    'category': category,
                    'created_at': now,
                    'last_accessed': now,
                    'access_count': 1,
                    'importance': min(max(1, importance), 10),
                    'expires': expires.isoformat() if expires else None,
                    'topics': topics or [],
                    'source': source
                }
            
            self._save_memories()
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Erinnerung: {e}")
            return False
    
    def recall(self, key: str, default: Any = None, update_access: bool = True) -> Any:
        """Ruft eine Information aus dem Langzeitgedächtnis ab.
        
        Args:
            key: Der Schlüssel der Information
            default: Standardwert, falls nicht gefunden
            update_access: Ob der Zugriffszeitpunkt aktualisiert werden soll
            
        Returns:
            Die gespeicherte Information oder der Standardwert
        """
        try:
            memory_id = hashlib.md5(key.encode('utf-8')).hexdigest()
            
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                
                # Prüfe auf Ablaufdatum
                if 'expires' in memory and memory['expires']:
                    expires = datetime.fromisoformat(memory['expires'])
                    if datetime.now() > expires:
                        del self.memories[memory_id]
                        self._save_memories()
                        return default
                
                # Zugriffszeitpunkt aktualisieren, falls gewünscht
                if update_access:
                    memory['last_accessed'] = datetime.now().isoformat()
                    memory['access_count'] = memory.get('access_count', 0) + 1
                    self._save_memories()
                
                return memory['value']
            
            return default
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Erinnerung: {e}")
            return default
    
    def forget(self, key: str) -> bool:
        """Löscht eine Information aus dem Langzeitgedächtnis.
        
        Args:
            key: Der Schlüssel der zu löschenden Information
            
        Returns:
            True wenn die Information gelöscht wurde, sonst False
        """
        try:
            memory_id = hashlib.md5(key.encode('utf-8')).hexdigest()
            if memory_id in self.memories:
                del self.memories[memory_id]
                self._save_memories()
                return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Erinnerung: {e}")
            return False
            
    def search_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Sucht nach Erinnerungen zu einem bestimmten Thema.
        
        Args:
            topic: Das gesuchte Thema
            limit: Maximale Anzahl von Ergebnissen
            
        Returns:
            Liste von passenden Erinnerungen, sortiert nach Relevanz
        """
        try:
            results = []
            topic_lower = topic.lower()
            
            for memory in self.memories.values():
                # Prüfe Themen
                memory_topics = [t.lower() for t in memory.get('topics', [])]
                if topic_lower in memory_topics or topic_lower in memory['key'].lower():
                    relevance = memory.get('importance', 5)  # Basis-Relevanz
                    
                    # Erhöhe Relevanz für kürzlich genutzte Einträge
                    last_accessed = datetime.fromisoformat(memory['last_accessed'])
                    days_since_access = (datetime.now() - last_accessed).days
                    if days_since_access < 7:  # Letzte Woche genutzt
                        relevance += 2
                    
                    results.append((relevance, memory))
            
            # Sortiere nach Relevanz und beschränke die Anzahl
            results.sort(key=lambda x: x[0], reverse=True)
            return [item[1] for item in results[:limit]]
            
        except Exception as e:
            logger.error(f"Fehler bei der Themensuche: {e}")
            return []
    
    def get_recent_memories(self, days: int = 7, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gibt kürzlich erstellte oder genutzte Erinnerungen zurück.
        
        Args:
            days: Zeitraum in Tagen
            category: Optionale Kategorie zur Filterung
            
        Returns:
            Liste von Erinnerungen, sortiert nach letztem Zugriff
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent = []
            
            for memory in self.memories.values():
                # Filter nach Kategorie, falls angegeben
                if category and memory.get('category') != category:
                    continue
                    
                # Prüfe Erstellungs- und Zugriffsdatum
                created = datetime.fromisoformat(memory['created_at'])
                accessed = datetime.fromisoformat(memory['last_accessed'])
                
                if created >= cutoff_date or accessed >= cutoff_date:
                    recent.append((accessed, memory))
            
            # Sortiere nach letztem Zugriff (neueste zuerst)
            recent.sort(key=lambda x: x[0], reverse=True)
            return [item[1] for item in recent]
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der letzten Erinnerungen: {e}")
            return []
    
    def get_memories_by_date_range(self, start_date: datetime, end_date: datetime, 
                                 category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gibt Erinnerungen in einem bestimmten Zeitraum zurück.
        
        Args:
            start_date: Anfangsdatum des Zeitraums
            end_date: Enddatum des Zeitraums
            category: Optionale Kategorie zur Filterung
            
        Returns:
            Liste von Erinnerungen im Zeitraum
        """
        try:
            results = []
            
            for memory in self.memories.values():
                # Filter nach Kategorie, falls angegeben
                if category and memory.get('category') != category:
                    continue
                    
                # Prüfe Erstellungsdatum
                created = datetime.fromisoformat(memory['created_at'])
                if start_date <= created <= end_date:
                    results.append((created, memory))
            
            # Sortiere nach Erstellungsdatum
            results.sort(key=lambda x: x[0])
            return [item[1] for item in results]
            
        except Exception as e:
            logger.error(f"Fehler bei der Datumsbereichssuche: {e}")
            return []
    
    def generate_weekly_summaries(self, categories: Optional[List[str]] = None, remember: bool = False, user_id: str = 'default') -> Dict[str, str]:
        """Create weekly summaries grouped by category."""
        categories = categories or ['support', 'lore', 'fragen']
        cutoff = datetime.now() - timedelta(days=7)
        summaries: Dict[str, str] = {}
        for category in categories:
            cat_lower = category.lower()
            entries: List[str] = []
            for memory in self.memories.values():
                if memory.get('category', '').lower() != cat_lower:
                    continue
                try:
                    created = datetime.fromisoformat(memory.get('created_at'))
                except Exception:
                    continue
                if created < cutoff:
                    continue
                value = memory.get('value')
                if isinstance(value, str):
                    snippet = value.strip()
                else:
                    snippet = json.dumps(value, ensure_ascii=False)
                if snippet:
                    entries.append(f'- {snippet}')
            if entries:
                header = f'Woechentliche Zusammenfassung ({category}):'
                summary_text = '\n'.join([header] + entries)
            else:
                summary_text = f'Woechentliche Zusammenfassung ({category}): Keine neuen Eintraege.'
            summaries[category] = summary_text
            if remember and entries:
                key = f"weekly_summary_{category.lower()}_{datetime.now().strftime('%Y-%m-%d')}"
                payload = {
                    'user': user_id,
                    'summary': summary_text,
                    'generated_at': datetime.now().isoformat(),
                    'category': category,
                }
                self.remember(key=key, value=payload, category='weekly_summary', importance=5, topics=[category], source='system')
        return summaries

    def get_memory_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über das Langzeitgedächtnis zurück.
        
        Returns:
            Dictionary mit verschiedenen Statistiken
        """
        stats = {
            'total_memories': len(self.memories),
            'categories': {},
            'oldest_memory': None,
            'newest_memory': None,
            'most_accessed': None
        }
        
        if not self.memories:
            return stats
        
        oldest = None
        newest = None
        most_accessed = None
        
        for memory in self.memories.values():
            # Kategorien zählen
            category = memory.get('category', 'uncategorized')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Älteste/Neueste Erinnerung finden
            created = datetime.fromisoformat(memory['created_at'])
            if oldest is None or created < oldest[0]:
                oldest = (created, memory)
            if newest is None or created > newest[0]:
                newest = (created, memory)
                
            # Meist genutzte Erinnerung finden
            access_count = memory.get('access_count', 0)
            if most_accessed is None or access_count > most_accessed[0]:
                most_accessed = (access_count, memory)
        
        stats.update({
            'oldest_memory': oldest[1] if oldest else None,
            'newest_memory': newest[1] if newest else None,
            'most_accessed': most_accessed[1] if most_accessed else None
        })
        
        return stats
    
    def search(self, query: str, category: Optional[str] = None, 
              limit: int = 5, min_importance: int = 0) -> List[Dict[str, Any]]:
        """Durchsucht das Langzeitgedächtnis nach relevanten Informationen.
        
        Args:
            query: Suchbegriff
            category: Optionale Kategorie zur Einschränkung
            limit: Maximale Anzahl von Ergebnissen
            min_importance: Minimale Wichtigkeit der Ergebnisse (1-10)
            
        Returns:
            Liste von passenden Einträgen
        """
        try:
            results = []
            query = query.lower()
            
            for memory_id, memory in self.memories.items():
                # Prüfe Kategorie, falls angegeben
                if category and memory.get('category') != category:
                    continue
                    
                # Prüfe Mindestwichtigkeit
                if memory.get('importance', 0) < min_importance:
                    continue
                
                # Prüfe Ablaufdatum
                if memory.get('expires'):
                    expires = datetime.fromisoformat(memory['expires'])
                    if datetime.now() > expires:
                        continue
                
                # Suche im Schlüssel und Wert
                key_matches = query in memory.get('key', '').lower()
                value_str = str(memory.get('value', '')).lower()
                value_matches = query in value_str
                
                if key_matches or value_matches:
                    # Berechne Relevanz (einfache Heuristik)
                    relevance = 0
                    if key_matches:
                        relevance += 10
                    if value_matches:
                        relevance += 1
                    
                    # Berücksichtige Zugriffshäufigkeit und Wichtigkeit
                    relevance += memory.get('access_count', 0) * 0.1
                    relevance += memory.get('importance', 5) * 0.5
                    
                    results.append({
                        **memory,
                        'relevance': relevance,
                        'id': memory_id
                    })
            
            # Sortiere nach Relevanz
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Fehler bei der Suche im Langzeitgedächtnis: {e}")
            return []
    
    def get_categories(self) -> List[str]:
        """Gibt eine Liste aller vorhandenen Kategorien zurück."""
        categories = set()
        for memory in self.memories.values():
            if 'category' in memory:
                categories.add(memory['category'])
        return list(categories)
    
    def cleanup_expired(self) -> int:
        """Entfernt abgelaufene Einträge.
        
        Returns:
            Anzahl der entfernten Einträge
        """
        count = 0
        now = datetime.now()
        
        memory_ids = list(self.memories.keys())
        for memory_id in memory_ids:
            memory = self.memories[memory_id]
            if 'expires' in memory and memory['expires']:
                expires = datetime.fromisoformat(memory['expires'])
                if now > expires:
                    del self.memories[memory_id]
                    count += 1
        
        if count > 0:
            self._save_memories()
            
        return count
