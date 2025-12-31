"""Weather Plugin for JARVIS - Wetter-Informationen abrufen"""

import os
import requests
import re
from typing import Dict, Any, Optional
from datetime import datetime

# Plugin Metadata
PLUGIN_NAME = "Wetter"
PLUGIN_DESCRIPTION = "Zeigt aktuelle Wetterinformationen und Vorhersagen an"
PLUGIN_VERSION = "1.0.2"
PLUGIN_AUTHOR = "Lautloserspieler"


class WeatherPlugin:
    """Plugin für Wetterabfragen mit OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.default_city = "Berlin"
        self.default_units = "metric"  # Celsius
        
    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Verarbeitet Wetter-Anfragen
        
        Beispiele:
        - "Wie ist das Wetter?"
        - "Wetter in München"
        - "Wie ist das Wetter in Limburg"
        - "Wettervorhersage Berlin"
        """
        command_lower = command.lower()
        
        # WICHTIG: Prüfe erst ob es eine Wetter-Anfrage ist!
        if not self._is_weather_request(command_lower):
            return None  # Nicht unsere Zuständigkeit
        
        print(f"[WEATHER] Processing weather request: {command[:50]}")
        
        # Stadt extrahieren
        city = self._extract_city(command_lower)
        
        if not city:
            city = self.default_city
        
        print(f"[WEATHER] Extracted city: {city}")
        
        # Aktuelle oder Vorhersage?
        if "vorhersage" in command_lower or "morgen" in command_lower:
            return self._get_forecast(city)
        else:
            return self._get_current_weather(city)
    
    def _is_weather_request(self, command: str) -> bool:
        """Prüft ob die Anfrage eine Wetter-Anfrage ist"""
        weather_triggers = [
            "wetter",
            "temperatur",
            "regen",
            "regnet",
            "schnee",
            "schneit",
            "sonne",
            "sonnig",
            "wolken",
            "wolkig",
            "gewitter",
            "vorhersage",
            "wettervorhersage",
            "wetteraussicht",
            "klima",
            "grad celsius",
            "°c",
        ]
        
        return any(trigger in command for trigger in weather_triggers)
    
    def _extract_city(self, command: str) -> Optional[str]:
        """Extrahiert Stadtname aus Befehl"""
        
        # Pattern 1: "in [Stadt]"
        match = re.search(r'\bin\s+([\wäöüß-]+)', command, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            return city.capitalize()
        
        # Pattern 2: "Wetter [Stadt]"
        match = re.search(r'wetter\s+([\wäöüß-]+)', command, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            # Filtere Stopwörter
            if city.lower() not in ['in', 'von', 'für', 'heute', 'morgen', 'ist']:
                return city.capitalize()
        
        # Pattern 3: "[Stadt]-Wetter"
        match = re.search(r'([\wäöüß-]+)-wetter', command, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            return city.capitalize()
        
        # Pattern 4: Bekannte Städte (Fallback)
        common_cities = [
            "berlin", "münchen", "hamburg", "köln", "frankfurt",
            "stuttgart", "düsseldorf", "dortmund", "essen", "leipzig",
            "bremen", "dresden", "hannover", "nürnberg", "duisburg",
            "limburg", "wiesbaden", "bonn", "mannheim", "karlsruhe",
            "augsburg", "freiburg", "lübeck", "rostock", "kiel"
        ]
        
        for city in common_cities:
            if city in command:
                return city.capitalize()
        
        return None
    
    def _get_current_weather(self, city: str) -> str:
        """Holt aktuelles Wetter"""
        if not self.api_key:
            return (
                "⚠️ OpenWeatherMap API-Key fehlt!\n\n"
                "Bitte setze die Umgebungsvariable:\n"
                "export OPENWEATHER_API_KEY='dein_api_key'\n\n"
                "Kostenlosen API-Key hier holen:\n"
                "https://openweathermap.org/api"
            )
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": self.default_units,
                "lang": "de"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Daten formatieren
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"].capitalize()
            wind_speed = data["wind"]["speed"]
            
            # Get actual city name from API response
            actual_city = data["name"]
            
            result = f"🌤️ Wetter in {actual_city}:\n\n"
            result += f"🌡️ Temperatur: {temp:.1f}°C (gefühlt {feels_like:.1f}°C)\n"
            result += f"☁️ Bedingungen: {description}\n"
            result += f"💧 Luftfeuchtigkeit: {humidity}%\n"
            result += f"💨 Windgeschwindigkeit: {wind_speed} m/s"
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return f"❌ Stadt '{city}' nicht gefunden. Bitte überprüfe die Schreibweise."
            return f"❌ HTTP-Fehler: {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"❌ Fehler beim Abrufen des Wetters: {str(e)}"
        except KeyError as e:
            return f"❌ Fehler beim Verarbeiten der Wetterdaten: {str(e)}"
    
    def _get_forecast(self, city: str) -> str:
        """Holt 3-Tage Wettervorhersage"""
        if not self.api_key:
            return (
                "⚠️ OpenWeatherMap API-Key fehlt!\n\n"
                "Siehe Anleitung bei aktuellem Wetter."
            )
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": self.default_units,
                "lang": "de"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            actual_city = data["city"]["name"]
            
            # 3 Tage (alle 8 Einträge = 1 Tag bei 3h Intervallen)
            result = f"📅 3-Tage Vorhersage für {actual_city}:\n\n"
            
            # Gruppiere nach Tagen
            days = {}
            for item in data["list"][:24]:  # 3 Tage * 8 Einträge
                date = datetime.fromtimestamp(item["dt"]).strftime("%A, %d.%m")
                if date not in days:
                    days[date] = {
                        "temps": [],
                        "descriptions": []
                    }
                days[date]["temps"].append(item["main"]["temp"])
                days[date]["descriptions"].append(item["weather"][0]["description"])
            
            # Formatiere Ausgabe
            for date, info in list(days.items())[:3]:
                avg_temp = sum(info["temps"]) / len(info["temps"])
                max_temp = max(info["temps"])
                min_temp = min(info["temps"])
                # Häufigste Beschreibung
                desc = max(set(info["descriptions"]), key=info["descriptions"].count)
                
                result += f"📆 {date}\n"
                result += f"   🌡️ {min_temp:.1f}°C - {max_temp:.1f}°C (Ø {avg_temp:.1f}°C)\n"
                result += f"   ☁️ {desc.capitalize()}\n\n"
            
            return result.strip()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return f"❌ Stadt '{city}' nicht gefunden."
            return f"❌ HTTP-Fehler: {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"❌ Fehler beim Abrufen der Vorhersage: {str(e)}"
        except KeyError as e:
            return f"❌ Fehler beim Verarbeiten der Vorhersage: {str(e)}"


# Plugin Instance für JARVIS
def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    plugin = WeatherPlugin()
    return plugin.process(command, context)


def health_check() -> Dict[str, Any]:
    """Health-Check für das Wetter-Plugin."""
    missing_keys = []
    if not os.getenv("OPENWEATHER_API_KEY"):
        missing_keys.append("openweather_api_key")

    status = "ok" if not missing_keys else "warning"
    return {
        "status": status,
        "missing_keys": missing_keys,
        "errors": []
    }
