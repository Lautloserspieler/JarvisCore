import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """Represents a piece of knowledge from an API source"""
    id: str
    content: Dict[str, Any]
    source: str
    timestamp: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class KnowledgeProcessor:
    """Processes, filters, and stores knowledge from multiple API sources"""
    
    def __init__(self, storage_dir: str = None, min_confirmations: int = 2):
        """
        Initialize the Knowledge Processor
        
        Args:
            storage_dir: Directory to store knowledge data
            min_confirmations: Minimum number of sources required to confirm knowledge
        """
        self.storage_dir = storage_dir or os.path.join('data', 'knowledge')
        self.min_confirmations = min_confirmations
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}
        self.source_counts: Dict[str, int] = {}
        self.confirmed_items: Dict[str, Set[str]] = {}  # item_id: set of source names
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Load existing knowledge if available
        self._load_knowledge()
    
    def _generate_id(self, content: Dict) -> str:
        """Generate a unique ID for a knowledge item based on its content"""
        # Create a stable string representation of the content
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _load_knowledge(self):
        """Load knowledge from storage"""
        knowledge_file = os.path.join(self.storage_dir, 'knowledge_base.json')
        try:
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = data.get('knowledge_base', {})
                    self.source_counts = data.get('source_counts', {})
                    # Convert confirmed_items lists back to sets
                    self.confirmed_items = {
                        k: set(v) for k, v in data.get('confirmed_items', {}).items()
                    }
                logger.info(f"Loaded {len(self.knowledge_base)} knowledge items from storage")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
    
    def save_knowledge(self):
        """Save knowledge to storage"""
        knowledge_file = os.path.join(self.storage_dir, 'knowledge_base.json')
        try:
            # Convert sets to lists for JSON serialization
            data = {
                'knowledge_base': self.knowledge_base,
                'source_counts': self.source_counts,
                'confirmed_items': {
                    k: list(v) for k, v in self.confirmed_items.items()
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Write to a temporary file first, then rename (atomic operation)
            temp_file = f"{knowledge_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # On Windows, we need to remove the destination file first if it exists
            if os.path.exists(knowledge_file):
                os.remove(knowledge_file)
            os.rename(temp_file, knowledge_file)
            
            logger.info(f"Saved {len(self.knowledge_base)} knowledge items to storage")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def process_api_response(self, source_name: str, response_data: List[Dict]) -> Tuple[int, int]:
        """
        Process API response and update knowledge base
        
        Args:
            source_name: Name of the API source
            response_data: List of items from the API response
            
        Returns:
            Tuple of (new_items, updated_items) counts
        """
        if not response_data or not isinstance(response_data, list):
            return 0, 0
        
        new_items = 0
        updated_items = 0
        
        for item_data in response_data:
            # Skip invalid items
            if not item_data or not isinstance(item_data, dict):
                continue
                
            # Generate a unique ID for this item
            item_id = self._generate_id(item_data)
            
            # Check if we already have this item
            if item_id in self.knowledge_base:
                existing_item = self.knowledge_base[item_id]
                
                # Check if this source already confirmed this item
                if source_name in self.confirmed_items.get(item_id, set()):
                    continue  # Already confirmed by this source
                
                # Update the existing item
                existing_item['last_updated'] = datetime.utcnow().isoformat()
                existing_item['sources'].append(source_name)
                existing_item['source_count'] = len(existing_item['sources'])
                
                # Update confidence based on number of sources
                existing_item['confidence'] = min(1.0, 0.5 + (0.1 * existing_item['source_count']))
                
                # Update confirmed items
                if item_id not in self.confirmed_items:
                    self.confirmed_items[item_id] = set()
                self.confirmed_items[item_id].add(source_name)
                
                updated_items += 1
            else:
                # Create a new knowledge item
                knowledge_item = {
                    'id': item_id,
                    'content': item_data,
                    'sources': [source_name],
                    'source_count': 1,
                    'first_seen': datetime.utcnow().isoformat(),
                    'last_updated': datetime.utcnow().isoformat(),
                    'confidence': 0.5,  # Initial confidence
                    'metadata': {
                        'confirmed': False,
                        'verification_count': 1
                    }
                }
                
                self.knowledge_base[item_id] = knowledge_item
                
                # Initialize confirmed items set
                self.confirmed_items[item_id] = {source_name}
                
                new_items += 1
        
        # Update source counts
        self.source_counts[source_name] = self.source_counts.get(source_name, 0) + len(response_data)
        
        # Save changes
        self.save_knowledge()
        
        return new_items, updated_items
    
    def get_confirmed_knowledge(self, min_confidence: float = 0.7) -> List[Dict]:
        """
        Get knowledge items that meet the minimum confirmation threshold
        
        Args:
            min_confidence: Minimum confidence score (0.0 to 1.0)
            
        Returns:
            List of confirmed knowledge items
        """
        confirmed = []
        
        for item_id, item in self.knowledge_base.items():
            if item['confidence'] >= min_confidence and item['source_count'] >= self.min_confirmations:
                confirmed_item = item.copy()
                confirmed_item['confirmed'] = True
                confirmed.append(confirmed_item)
        
        # Sort by confidence (highest first) and then by number of sources
        confirmed.sort(key=lambda x: (-x['confidence'], -x['source_count']))
        return confirmed
    
    def search_knowledge(self, query: str, field: str = None, min_confidence: float = 0.0) -> List[Dict]:
        """
        Search the knowledge base
        
        Args:
            query: Search query string
            field: Specific field to search in (None searches all fields)
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching knowledge items
        """
        query = query.lower()
        results = []
        
        for item in self.knowledge_base.values():
            if item['confidence'] < min_confidence:
                continue
                
            content = item['content']
            
            # If a specific field is specified, only search that field
            if field:
                if field in content and isinstance(content[field], str):
                    if query in content[field].lower():
                        results.append(item)
            else:
                # Search all string fields in the content
                for value in content.values():
                    if isinstance(value, str) and query in value.lower():
                        results.append(item)
                        break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        confirmed = self.get_confirmed_knowledge()
        
        return {
            'total_items': len(self.knowledge_base),
            'confirmed_items': len(confirmed),
            'sources': self.source_counts,
            'confidence_distribution': self._get_confidence_distribution(),
            'last_updated': max(
                [item['last_updated'] for item in self.knowledge_base.values()],
                default='Never'
            )
        }
    
    def _get_confidence_distribution(self) -> Dict[str, int]:
        """Get distribution of confidence scores"""
        distribution = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for item in self.knowledge_base.values():
            conf = item['confidence']
            if conf < 0.2:
                distribution['0.0-0.2'] += 1
            elif conf < 0.4:
                distribution['0.2-0.4'] += 1
            elif conf < 0.6:
                distribution['0.4-0.6'] += 1
            elif conf < 0.8:
                distribution['0.6-0.8'] += 1
            else:
                distribution['0.8-1.0'] += 1
        
        return distribution

# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the knowledge processor
    processor = KnowledgeProcessor(min_confirmations=2)
    
    # Example: Process data from Wikipedia (German)
    wikipedia_data = [
        {
            "title": "Künstliche Intelligenz",
            "extract": "Künstliche Intelligenz (KI) ist ein Teilgebiet der Informatik...",
            "url": "https://de.wikipedia.org/wiki/K%C3%BCnstliche_Intelligenz"
        },
        {
            "title": "Maschinelles Lernen",
            "extract": "Maschinelles Lernen ist ein Teilgebiet der künstlichen Intelligenz...",
            "url": "https://de.wikipedia.org/wiki/Maschinelles_Lernen"
        }
    ]
    
    # Process data from first source
    new, updated = processor.process_api_response("wikipedia_de", wikipedia_data)
    print(f"Added {new} new items, updated {updated} existing items")
    
    # Example: Process similar data from another source (e.g., Wikidata)
    wikidata_data = [
        {
            "title": "Künstliche Intelligenz",
            "description": "Forschungsgebiet der Informatik, das sich mit der Automatisierung intelligenten Verhaltens befasst",
            "url": "https://www.wikidata.org/wiki/Q11660"
        },
        {
            "title": "Neuronales Netz",
            "description": "Netzwerk aus künstlichen Neuronen",
            "url": "https://www.wikidata.org/wiki/Q187658"
        }
    ]
    
    # Process data from second source
    new, updated = processor.process_api_response("wikidata", wikidata_data)
    print(f"Added {new} new items, updated {updated} existing items")
    
    # Get confirmed knowledge
    confirmed = processor.get_confirmed_knowledge()
    print(f"\nConfirmed knowledge items:")
    for item in confirmed:
        print(f"- {item['content'].get('title')} (Confidence: {item['confidence']:.2f}, Sources: {item['source_count']})")
    
    # Get statistics
    stats = processor.get_stats()
    print(f"\nKnowledge Base Statistics:")
    print(f"Total items: {stats['total_items']}")
    print(f"Confirmed items: {stats['confirmed_items']}")
    print(f"Confidence distribution: {stats['confidence_distribution']}")
