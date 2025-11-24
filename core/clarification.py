"""
Modul für die Klarstellungslogik des J.A.R.V.I.S. Systems
"""
import re
from typing import List, Dict, Any, Set, Tuple

class ClarificationHandler:
    """Behandelt Klarstellungen bei unklaren Benutzereingaben"""
    
    def __init__(self, logger=None):
        """Initialisiert den ClarificationHandler"""
        self.logger = logger or print
        
    def needs_clarification(self, response: str) -> bool:
        """Bestimmt mit natürlicher Sprachverarbeitung, ob eine Klarstellung erforderlich ist"""
        # Erweiterte Heuristik mit natürlichsprachigen Phrasen
        uncertainty_phrases = [
            # Direkte Unklarheiten
            "ich bin mir nicht sicher", "ich verstehe nicht ganz", 
            "könntest du das genauer erklären", "was meinst du damit",
            "das ist mir nicht ganz klar", "könntest du das bitte präzisieren",
            
            # Vage Formulierungen
            "vielleicht", "möglicherweise", "eventuell", "könnte sein",
            "ich glaube", "ich denke", "vielleicht so etwas wie",
            
            # Fragen nach Klarstellung
            "was genau meinst du mit", "welche art von", 
            "könntest du mir ein beispiel geben", "wie meinst du das",
            
            # Unbestimmte Pronomen
            "man könnte", "es wäre möglich", "das wäre eine option"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in uncertainty_phrases)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrahiert Schlüsselwörter aus einem Text"""
        # Entferne Satzzeichen und mache den Text klein
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Liste von Stoppwörtern, die ignoriert werden sollen
        stop_words = {
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'eines',
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie', 'mir', 'mich', 'dir', 'dich',
            'sich', 'und', 'oder', 'aber', 'weil', 'dass', 'wenn', 'dann', 'als', 'wie', 'zu',
            'vom', 'zum', 'zur', 'für', 'mit', 'von', 'bei', 'nach', 'aus', 'über', 'unter',
            'hinter', 'neben', 'zwischen', 'durch', 'gegen', 'um', 'an', 'in', 'auf', 'vor',
            'hast', 'hat', 'habe', 'haben', 'hatte', 'hatten', 'war', 'waren', 'bin', 'bist',
            'ist', 'sind', 'warst', 'wart', 'war', 'waren', 'werde', 'wirst', 'wird', 'werden',
            'würde', 'würdest', 'würden', 'würdet', 'kann', 'kannst', 'können', 'könnt',
            'soll', 'sollst', 'sollen', 'sollt', 'mag', 'magst', 'mögen', 'mögt', 'muss',
            'musst', 'müssen', 'müsst', 'darf', 'darfst', 'dürfen', 'dürft', 'will', 'willst',
            'wollen', 'wollt', 'nicht', 'auch', 'schon', 'noch', 'nur', 'erst', 'etwas',
            'nichts', 'alles', 'viel', 'wenig', 'mehr', 'weniger', 'sehr', 'ganz', 'gar',
            'so', 'wie', 'als', 'denn', 'doch', 'ja', 'nein', 'bitte', 'danke', 'okay', 
            'ok', 'hey', 'hallo', 'tschüss', 'auf wiedersehen'
        }
        
        # Teile den Text in Wörter auf und entferne Stoppwörter
        words = [word for word in text.split() if word not in stop_words and len(word) > 2]
        
        # Zähle die Häufigkeit jedes Wortes
        word_count = {}
        for word in words:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1
        
        # Sortiere die Wörter nach Häufigkeit (absteigend) und gib die Top 5 zurück
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:5]]
    
    def get_similar_commands(self, query: str) -> List[str]:
        """Findet ähnliche Befehle basierend auf der Abfrage mit natürlicher Sprache"""
        keywords = self.extract_keywords(query)
        if not keywords:
            return []
            
        # Natürlicher klingende Befehlskategorien mit Beispielen
        command_categories = {
            'system': [
                'den Computer herunterfahren', 'das System neu starten',
                'in den Ruhemodus wechseln', 'den Bildschirm sperren',
                'mich abmelden', 'den Benutzer wechseln'
            ],
            'anwendung': [
                'eine Anwendung öffnen', 'ein Programm starten',
                'eine App schließen', 'ein Programm beenden',
                'ein anderes Programm öffnen'
            ],
            'suche': [
                'im Internet suchen', 'etwas für mich finden',
                'Informationen zu einem Thema suchen',
                'im Web nach etwas Bestimmtem suchen'
            ],
            'einstellung': [
                'die Lautstärke anpassen', 'die Helligkeit ändern',
                'die WLAN-Einstellungen öffnen', 'Bluetooth ein- oder ausschalten',
                'die Systemeinstellungen öffnen'
            ],
            'datei': [
                'eine Datei öffnen', 'einen Ordner durchsuchen',
                'ein Dokument speichern', 'Bilder anzeigen',
                'Musik abspielen', 'ein Video öffnen'
            ],
            'zeit': [
                'die aktuelle Uhrzeit wissen', 'das heutige Datum anzeigen',
                'den Kalender öffnen', 'eine Erinnerung erstellen',
                'einen Wecker stellen'
            ],
            'wetter': [
                'die Wettervorhersage abrufen',
                'die aktuelle Temperatur anzeigen',
                'den Wetterbericht für morgen anzeigen',
                'die Regenwahrscheinlichkeit überprüfen'
            ],
            'rechner': [
                'eine Berechnung durchführen', 'etwas ausrechnen',
                'eine mathematische Formel lösen',
                'Prozentwerte berechnen'
            ]
        }
        
        # Verbesserte Kategorie-Erkennung mit natürlichen Sprachmustern
        category_patterns = {
            'system': r'(herunterfahren|neustarten|abschalten|ruhezustand|sperren|abmelden|benutzer)',
            'anwendung': r'(öffn|start|schließ|beend|programm|app|anwendung)',
            'suche': r'(such|find|zeig mir|information|google|web)',
            'einstellung': r'(einstellung|konfiguration|wlan|bluetooth|lautstärke|helligkeit|wifi|netzwerk)',
            'datei': r'(datei|ordner|dokument|bild|musik|video|speicher|öffne|speichern)',
            'zeit': r'(uhr|zeit|datum|kalender|termin|erinnerung|wecker|stunde|minute|sekunde)',
            'wetter': r'(wetter|temperatur|regen|sonne|wolke|vorhersage|warm|kalt)',
            'rechner': r'(rechn|berechn|plus|minus|mal|geteilt|wurzel|quadrat|prozent|mathe)'
        }
        
        # Finde passende Kategorien basierend auf natürlichsprachigen Mustern
        matched_categories = set()
        query_lower = query.lower()
        
        for category, pattern in category_patterns.items():
            if re.search(pattern, query_lower):
                matched_categories.add(category)
        
        # Wenn keine Kategorie gefunden wurde, versuche es mit einer allgemeineren Suche
        if not matched_categories:
            for keyword in keywords:
                for category, terms in command_categories.items():
                    if any(term in keyword for term in category_patterns[category].split('|')):
                        matched_categories.add(category)
        
        # Generiere natürlich klingende Vorschläge
        suggestions = []
        for category in matched_categories:
            suggestions.extend(command_categories[category])
        
        # Entferne Duplikate und behalte die Reihenfolge bei
        seen = set()
        unique_suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]
        
        # Wähle zufällig maximal 3 Vorschläge aus, um Abwechslung zu bieten
        import random
        if len(unique_suggestions) > 3:
            return random.sample(unique_suggestions, 3)
        return unique_suggestions
    
    def generate_clarification_options(self, query: str, response: str) -> List[str]:
        """Generiert mögliche Klarstellungen basierend auf der Abfrage und Antwort"""
        # Verwende die erweiterte Methode, um ähnliche Befehle zu finden
        similar_commands = self.get_similar_commands(query)
        
        # Wenn wir spezifische Vorschläge haben, geben wir diese zurück
        if similar_commands:
            return similar_commands[:3]  # Maximal 3 Vorschläge
        
        # Ansonsten verwenden wir eine generische Rückfrage
        return [
            'Könntest du das genauer erklären?',
            'Meinst du etwas Bestimmtes damit?',
            'Ich brauche mehr Informationen, um dir zu helfen.'
        ]
    
    def format_clarification_question(self, options: List[str]) -> str:
        """Formatiert die Klarstellungsfrage an den Benutzer in natürlicher Sprache"""
        if not options:
            return "Entschuldigen Sie, das habe ich nicht ganz verstanden. Könnten Sie das bitte etwas genauer beschreiben?"
        
        # Natürlichere Einleitung mit Variationen
        intros = [
            "Ich möchte sichergehen, dass ich Sie richtig verstehe. Meinten Sie vielleicht...",
            "Ich bin mir nicht ganz sicher. Könnten Sie damit gemeint haben...",
            "Um Ihnen besser helfen zu können, brauche ich eine kleine Präzisierung. Geht es um..."
        ]
        
        import random
        question = f"{random.choice(intros)}\n\n"
        
        # Natürlichere Aufzählung der Optionen
        if len(options) == 1:
            return f"{question}Meinen Sie damit: '{options[0]}'?"
            
        for i, option in enumerate(options, 1):
            # Verwende verschiedene Formulierungen für die Aufzählung
            if i == len(options):
                question += f"Oder meinten Sie vielleicht: {option}?"
            else:
                question += f"- {option}\n"
        
        # Natürlichere Aufforderung zur Antwort
        follow_ups = [
            "\n\nBitte bestätigen Sie eine der genannten Möglichkeiten oder beschreiben Sie es genauer.",
            "\n\nKönnen Sie mir bitte sagen, welche dieser Möglichkeiten zutrifft?",
            "\n\nIch würde mich freuen, wenn Sie mir sagen könnten, was genau Sie benötigen."
        ]
        question += random.choice(follow_ups)
        
        return question
