"""
Wissens-API für J.A.R.V.I.S.
Ermöglicht den Zugriff auf verschiedene Wissensquellen wie Wikipedia, Open Library und DBpedia.
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Any, Union
import requests
import wikipediaapi
import isbnlib
from urllib.parse import quote, unquote
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from utils.logger import Logger

class WissensAPI:
    """
    Eine zentrale Klasse für den Zugriff auf verschiedene Wissensquellen wie Wikipedia und Open Library.
    """
    
    def __init__(self, sprache: str = 'de'):
        """
        Initialisiert die Wissens-API.
        
        Args:
            sprache: Die Sprache für die Suchergebnisse (z.B. 'de' für Deutsch, 'en' für Englisch)
        """
        self.logger = Logger()
        self.sprache = sprache
        self.timeout = 10  # Timeout in Sekunden für API-Aufrufe
        
        # Wikipedia-API mit Timeout konfigurieren
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language=sprache,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='JarvisKI/1.0',
            timeout=self.timeout
        )
        
        # Requests-Session mit Timeout konfigurieren
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JarvisKI/1.0',
            'Accept': 'application/json'
        })
        
        # Timeout für alle Requests in der Session setzen
        self.session.request = lambda method, url, **kwargs: (
            self.session.original_request(
                method, 
                url, 
                timeout=self.timeout, 
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )
        )
        self.session.original_request = self.session.request
        
        # Cache für häufig abgerufene Informationen
        self.cache: Dict[str, Any] = {}
        
        # SPARQL-Endpunkte
        self.dbpedia_endpoint = "https://dbpedia.org/sparql"
        self.conceptnet_endpoint = "https://api.conceptnet.io"
        self.open_library_url = "https://openlibrary.org"
        self.benutzer_agent = "JarvisKI/1.0"

    def suche_wikipedia(self, suchbegriff: str, zusaetzliche_info: bool = False) -> Dict[str, Any]:
        """
        Sucht nach einem Begriff in der Wikipedia.
        
        Args:
            suchbegriff: Der zu suchende Begriff
            zusaetzliche_info: Wenn True, werden zusätzliche Informationen abgerufen
            
        Returns:
            Ein Dictionary mit den Suchergebnissen
        """
        cache_key = f"wiki_{suchbegriff}_{zusaetzliche_info}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        ergebnis = {
            'erfolg': False,
            'titel': '',
            'zusammenfassung': '',
            'url': '',
            'kategorien': [],
            'zusaetzliche_infos': {},
            'fehler': None
        }
        
        def fetch_wiki():
            try:
                # Suche nach der Seite mit Timeout
                seite = self.wiki_wiki.page(suchbegriff)
                
                if seite.exists():
                    ergebnis.update({
                        'erfolg': True,
                        'titel': seite.title,
                        'zusammenfassung': seite.summary[:500] + '...' if len(seite.summary) > 500 else seite.summary,
                        'url': seite.fullurl,
                        'kategorien': list(seite.categories.keys())[:5]  # Erste 5 Kategorien
                    })
                    
                    # Zusätzliche Informationen abrufen, wenn gewünscht
                    if zusaetzliche_info:
                        ergebnis['zusaetzliche_infos'] = {
                            'seiten_id': seite.pageid,
                            'letzte_aenderung': seute.last_rev_timestamp,
                            'laenge_text': len(seite.text)
                        }
                else:
                    ergebnis['fehler'] = f"Keine Ergebnisse für '{suchbegriff}' gefunden"
            
            except requests.exceptions.Timeout:
                ergebnis['fehler'] = "Zeitüberschreitung bei der Wikipedia-Anfrage"
            except Exception as e:
                ergebnis['fehler'] = f"Fehler bei der Wikipedia-Suche: {str(e)}"
        
        # Führe die Abfrage in einem Thread mit Timeout aus
        thread = threading.Thread(target=fetch_wiki)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            ergebnis['fehler'] = "Zeitüberschreitung bei der Anfrage an die Wikipedia-API"
        
        if ergebnis.get('fehler'):
            self.logger.error(f"Fehler bei der Wikipedia-Suche nach '{suchbegriff}': {ergebnis['fehler']}")
        
        self.cache[cache_key] = ergebnis
        return ergebnis

    def verifiziere_antwort(self, frage: str, antwort: str) -> Dict[str, Any]:
        """
        Überprüft eine gegebene Antwort gegen mehrere Wissensquellen.
        
        Args:
            frage: Die ursprüngliche Frage
            antwort: Die zu überprüfende Antwort
            
        Returns:
            Ein Dictionary mit den Verifikationsergebnissen
        """
        ergebnisse = {
            'frage': frage,
            'vorgeschlagene_antwort': antwort,
            'quellen': [],
            'uebereinstimmungen': 0,
            'warnungen': [],
            'verifiziert': False
        }
        
        # 1. Überprüfung mit Wikipedia
        try:
            wiki_ergebnis = self.suche_wikipedia(antwort)
            if wiki_ergebnis['erfolg']:
                ergebnisse['quellen'].append({
                    'quelle': 'wikipedia',
                    'titel': wiki_ergebnis.get('titel', ''),
                    'zusammenfassung': wiki_ergebnis.get('zusammenfassung', '')
                })
                ergebnisse['uebereinstimmungen'] += 1
        except Exception as e:
            self.logger.warning(f"Fehler bei der Wikipedia-Überprüfung: {e}")
        
        # 2. Überprüfung mit DBpedia (für Personen und Orte)
        try:
            # Prüfen, ob es sich um eine Person handeln könnte
            if any(titel in frage.lower() for titel in ['wer ist', 'wer war', 'wer sind']):
                personenname = ' '.join(frage.split(' ')[2:])  # Extrahiere den Namen aus der Frage
                dbpedia_ergebnis = self.hole_personendaten(personenname)
                if dbpedia_ergebnis['erfolg']:
                    ergebnisse['quellen'].append({
                        'quelle': 'dbpedia',
                        'typ': 'person',
                        'daten': dbpedia_ergebnis
                    })
                    ergebnisse['uebereinstimmungen'] += 1
            # Prüfen auf Ortsinformationen
            elif any(titel in frage.lower() for titel in ['wo liegt', 'was ist', 'wie groß ist']):
                ortsname = ' '.join(frage.split(' ')[2:])  # Extrahiere den Ortsnamen
                dbpedia_ergebnis = self.hole_ortsinformationen(ortsname)
                if dbpedia_ergebnis['erfolg']:
                    ergebnisse['quellen'].append({
                        'quelle': 'dbpedia',
                        'typ': 'ort',
                        'daten': dbpedia_ergebnis
                    })
                    ergebnisse['uebereinstimmungen'] += 1
        except Exception as e:
            self.logger.warning(f"Fehler bei der DBpedia-Überprüfung: {e}")
        
        # 3. Überprüfung mit ConceptNet für allgemeine Konzepte
        try:
            konzepte = self.hole_konzepte(antwort)
            if konzepte['erfolg'] and len(konzepte.get('beziehungen', [])) > 0:
                ergebnisse['quellen'].append({
                    'quelle': 'conceptnet',
                    'beziehungen': konzepte.get('beziehungen', [])
                })
                ergebnisse['uebereinstimmungen'] += 1
        except Exception as e:
            self.logger.warning(f"Fehler bei der ConceptNet-Überprüfung: {e}")
        
        # 4. Überprüfung der Konsistenz der Quellen
        if ergebnisse['uebereinstimmungen'] >= 2:
            ergebnisse['verifiziert'] = True
        else:
            ergebnisse['warnungen'].append("Weniger als zwei unabhängige Quellen bestätigen diese Information.")
        
        return ergebnisse

    def beantworte_frage(self, frage: str) -> Dict[str, Any]:
        """
        Beantwortet eine Frage unter Verwendung mehrerer Quellen zur Verifizierung.
        
        Args:
            frage: Die zu beantwortende Frage
            
        Returns:
            Ein Dictionary mit der Antwort und Verifizierungsinformationen
        """
        # 1. Versuche eine direkte Antwort zu finden
        direkte_antwort = self._finde_direkte_antwort(frage)
        
        if direkte_antwort['erfolg']:
            # 2. Wenn eine direkte Antwort gefunden wurde, verifiziere sie
            verifizierung = self.verifiziere_antwort(frage, direkte_antwort['antwort'])
            
            if verifizierung['verifiziert']:
                return {
                    'erfolg': True,
                    'frage': frage,
                    'antwort': direkte_antwort['antwort'],
                    'verifiziert': True,
                    'quellen': [q['quelle'] for q in verifizierung['quellen']],
                    'details': verifizierung
                }
            else:
                return {
                    'erfolg': True,
                    'frage': frage,
                    'antwort': direkte_antwort['antwort'],
                    'verifiziert': False,
                    'warnung': 'Antwort konnte nicht durch mindestens zwei unabhängige Quellen verifiziert werden',
                    'details': verifizierung
                }
        
        # 3. Wenn keine direkte Antwort gefunden wurde, suche nach verwandten Informationen
        return {
            'erfolg': False,
            'frage': frage,
            'fehler': 'Es konnte keine ausreichend verifizierte Antwort gefunden werden',
            'vorschlaege': self._finde_verwandte_informationen(frage)
        }
    
    def _finde_direkte_antwort(self, frage: str) -> Dict[str, Any]:
        """Hilfsmethode zum Finden einer direkten Antwort auf eine Frage."""
        # Erste Priorität: Wikipedia
        wiki_ergebnis = self.suche_wikipedia(frage)
        if wiki_ergebnis['erfolg']:
            return {
                'erfolg': True,
                'quelle': 'wikipedia',
                'antwort': wiki_ergebnis['zusammenfassung'],
                'details': wiki_ergebnis
            }
        
        # Zweite Priorität: DBpedia für Personen und Orte
        if any(titel in frage.lower() for titel in ['wer ist', 'wer war', 'wer sind']):
            personenname = ' '.join(frage.split(' ')[2:])
            person_ergebnis = self.hole_personendaten(personenname)
            if person_ergebnis['erfolg']:
                return {
                    'erfolg': True,
                    'quelle': 'dbpedia',
                    'antwort': f"{person_ergebnis.get('beschreibung', '')} {', '.join(person_ergebnis.get('beruf', []))}",
                    'details': person_ergebnis
                }
        
        # Wenn keine direkte Antwort gefunden wurde
        return {'erfolg': False, 'fehler': 'Keine direkte Antwort gefunden'}
    
    def _finde_verwandte_informationen(self, frage: str) -> List[Dict[str, Any]]:
        """Hilfsmethode zum Finden verwandter Informationen zu einer Frage."""
        vorschlaege = []
        
        # Suche nach verwandten Konzepten
        konzepte = self.hole_konzepte(frage.split(' ')[0])
        if konzepte['erfolg'] and konzepte.get('verwandte_konzepte'):
            vorschlaege.append({
                'typ': 'verwandte_konzepte',
                'konzepte': konzepte['verwandte_konzepte'][:3]  # Erste 3 verwandte Konzepte
            })
        
        # Suche nach Büchern zum Thema
        buecher = self.suche_buecher_nach_titel(frage, limit=2)
        if buecher['erfolg'] and buecher.get('ergebnisse'):
            vorschlaege.append({
                'typ': 'buecher',
                'buecher': buecher['ergebnisse']
            })
        
        return vorschlaege


def health_check() -> Dict[str, Any]:
    """Health-Check für die Wissens-API."""
    return {
        "status": "ok",
        "missing_keys": [],
        "errors": []
    }

# Beispielverwendung
if __name__ == "__main__":
    wissens_api = WissensAPI()
    
    # Beispiel: Verifizierte Antwort auf eine Frage
    frage = "Wer ist Angela Merkel?"
    ergebnis = wissens_api.beantworte_frage(frage)
    
    if ergebnis['erfolg']:
        print(f"Frage: {ergebnis['frage']}")
        print(f"Antwort: {ergebnis['antwort']}")
        print(f"Verifiziert: {'Ja' if ergebnis['verifiziert'] else 'Nein'}")
        print(f"Quellen: {', '.join(ergebnis['quellen'])}")
    else:
        print(f"Keine ausreichende Antwort gefunden: {ergebnis.get('fehler', 'Unbekannter Fehler')}")
        if 'vorschlaege' in ergebnis:
            print("\nVorschläge für weitere Recherche:")
            for vorschlag in ergebnis['vorschlaege']:
                if vorschlag['typ'] == 'verwandte_konzepte':
                    print(f"Verwandte Konzepte: {', '.join(vorschlag['konzepte'])}")
                elif vorschlag['typ'] == 'buecher':
                    print("Bücher zum Thema:")
                    for buch in vorschlag['buecher']:
                        print(f"- {buch['titel']} von {', '.join(buch['autoren'])}")
