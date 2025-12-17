"""News Plugin for JARVIS - Nachrichten aus RSS-Feeds"""

import feedparser
from datetime import datetime
from typing import Dict, Any, Optional, List
import re

# Plugin Metadata
PLUGIN_NAME = "Nachrichten"
PLUGIN_DESCRIPTION = "Zeigt aktuelle Nachrichten aus RSS-Feeds an"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class NewsPlugin:
    """Plugin für Nachrichten aus RSS-Feeds"""
    
    def __init__(self):
        # Deutsche Nachrichten-Feeds
        self.feeds = {
            "tagesschau": "https://www.tagesschau.de/xml/rss2/",
            "heise": "https://www.heise.de/rss/heise-atom.xml",
            "spiegel": "https://www.spiegel.de/schlagzeilen/tops/index.rss",
            "zeit": "https://newsfeed.zeit.de/index",
            "golem": "https://rss.golem.de/rss.php?feed=RSS2.0",
            "tech": "https://www.heise.de/newsticker/heise-atom.xml",
        }
        
        self.categories = {
            "allgemein": ["tagesschau", "spiegel", "zeit"],
            "technik": ["heise", "golem", "tech"],
            "tech": ["heise", "golem"],
            "technologie": ["heise", "golem"],
        }
    
    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Verarbeitet Nachrichten-Anfragen
        
        Beispiele:
        - "Zeige Nachrichten"
        - "Was sind die Top-News?"
        - "Nachrichten über Technik"
        - "Tech News"
        - "Tagesschau Nachrichten"
        """
        command_lower = command.lower()
        
        # Kategorie oder Feed extrahieren
        category = self._extract_category(command_lower)
        feed_name = self._extract_feed(command_lower)
        
        # Anzahl extrahieren
        count = self._extract_count(command_lower)
        if not count:
            count = 5  # Default: 5 Artikel
        
        if feed_name:
            return self._get_news_from_feed(feed_name, count)
        elif category:
            return self._get_news_by_category(category, count)
        else:
            # Default: Allgemeine Nachrichten
            return self._get_news_by_category("allgemein", count)
    
    def _extract_category(self, command: str) -> Optional[str]:
        """Extrahiert Kategorie aus Befehl"""
        for category in self.categories.keys():
            if category in command:
                return category
        return None
    
    def _extract_feed(self, command: str) -> Optional[str]:
        """Extrahiert Feed-Namen aus Befehl"""
        for feed_name in self.feeds.keys():
            if feed_name in command:
                return feed_name
        return None
    
    def _extract_count(self, command: str) -> Optional[int]:
        """Extrahiert Anzahl aus Befehl"""
        # Suche nach "top 5", "5 nachrichten", etc.
        patterns = [
            r'top\s+(\d+)',
            r'(\d+)\s+nachricht',
            r'(\d+)\s+artikel',
            r'letzte\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _get_news_from_feed(self, feed_name: str, count: int) -> str:
        """Holt Nachrichten von einem spezifischen Feed"""
        if feed_name not in self.feeds:
            return f"❌ Unbekannter Feed: {feed_name}"
        
        feed_url = self.feeds[feed_name]
        
        try:
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                return f"ℹ️ Keine Artikel gefunden in {feed_name.capitalize()}"
            
            result = f"📰 {feed_name.capitalize()} - Top {min(count, len(feed.entries))} Nachrichten:\n\n"
            
            for i, entry in enumerate(feed.entries[:count], 1):
                title = self._clean_html(entry.title)
                link = entry.link if hasattr(entry, 'link') else ""
                
                # Datum formatieren
                pub_date = ""
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        dt = datetime(*entry.published_parsed[:6])
                        pub_date = dt.strftime("%d.%m %H:%M")
                    except:
                        pass
                
                result += f"{i}. {title}"
                if pub_date:
                    result += f" ({pub_date})"
                result += f"\n   🔗 {link}\n\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Fehler beim Abrufen von {feed_name}: {str(e)}"
    
    def _get_news_by_category(self, category: str, count: int) -> str:
        """Holt Nachrichten aus mehreren Feeds einer Kategorie"""
        if category not in self.categories:
            return f"❌ Unbekannte Kategorie: {category}"
        
        feed_names = self.categories[category]
        all_entries = []
        
        # Sammle Artikel von allen Feeds der Kategorie
        for feed_name in feed_names:
            feed_url = self.feeds[feed_name]
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:  # Max 3 pro Feed
                    all_entries.append({
                        "title": self._clean_html(entry.title),
                        "link": entry.link if hasattr(entry, 'link') else "",
                        "source": feed_name.capitalize(),
                        "published": entry.published_parsed if hasattr(entry, 'published_parsed') else None
                    })
            except Exception as e:
                print(f"Fehler bei {feed_name}: {e}")
                continue
        
        if not all_entries:
            return f"ℹ️ Keine Nachrichten in Kategorie '{category}' gefunden"
        
        # Sortiere nach Datum (neueste zuerst)
        all_entries.sort(
            key=lambda x: x['published'] if x['published'] else (0,0,0,0,0,0),
            reverse=True
        )
        
        result = f"📰 {category.capitalize()} - Top {min(count, len(all_entries))} Nachrichten:\n\n"
        
        for i, entry in enumerate(all_entries[:count], 1):
            pub_date = ""
            if entry['published']:
                try:
                    dt = datetime(*entry['published'][:6])
                    pub_date = dt.strftime("%d.%m %H:%M")
                except:
                    pass
            
            result += f"{i}. {entry['title']}"
            if pub_date:
                result += f" ({pub_date})"
            result += f"\n   📍 {entry['source']}"
            result += f"\n   🔗 {entry['link']}\n\n"
        
        return result.strip()
    
    def _clean_html(self, text: str) -> str:
        """Entfernt HTML-Tags aus Text"""
        # Einfache HTML-Tag Entfernung
        clean = re.sub(r'<[^>]+>', '', text)
        # HTML-Entities dekodieren
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&apos;', "'")
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        return clean.strip()


# Plugin Instance
def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    plugin = NewsPlugin()
    return plugin.process(command, context)
