"""Weather Plugin for JARVIS - Wetter-Informationen abrufen"""

import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Plugin Metadata
PLUGIN_NAME = "Wetter"
PLUGIN_DESCRIPTION = "Zeigt aktuelle Wetterinformationen und Vorhersagen an"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class WeatherPlugin:
    """Plugin für Wetterabfragen mit OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.default_city = "Berlin"
        self.default_units = "metric"  # Celsius
        
    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Verarbeitet Wetter-Anfragen
        
        Beispiele:
        - "Wie ist das Wetter?"
        - "Wetter in München"
        - "Wettervorhersage Berlin"
        """
        command_lower = command.lower()
        
        # Stadt extrahieren
        city = self._extract_city(command_lower)
        
        if not city:
            city = self.default_city
        
        # Aktuelle oder Vorhersage?
        if "vorhersage" in command_lower or "morgen" in command_lower:
            return self._get_forecast(city)
        else:
            return self._get_current_weather(city)
    
    def _extract_city(self, command: str) -> Optional[str]:
        """Extrahiert Stadtname aus Befehl"""
        cities = [
            "berlin", "münchen", "hamburg", "köln", "frankfurt",
            "stuttgart", "düsseldorf", "dortmund", "essen", "leipzig",
            "bremen", "dresden", "hannover", "nürnberg", "duisburg"
        ]
        
        for city in cities:
            if city in command:
                return city.capitalize()
        
        # Versuche "in X" Pattern
        if " in " in command:
            parts = command.split(" in ")
            if len(parts) > 1:
                city_part = parts[1].strip().split()[0]
                return city_part.capitalize()
        
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
            
            result = f"🌤️ Wetter in {city}:\n\n"
            result += f"🌡️ Temperatur: {temp:.1f}°C (gefühlt {feels_like:.1f}°C)\n"
            result += f"☁️ Bedingungen: {description}\n"
            result += f"💧 Luftfeuchtigkeit: {humidity}%\n"
            result += f"💨 Windgeschwindigkeit: {wind_speed} m/s"
            
            return result
            
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
            
            # 3 Tage (alle 8 Einträge = 1 Tag bei 3h Intervallen)
            result = f"📅 3-Tage Vorhersage für {city}:\n\n"
            
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
            
        except requests.exceptions.RequestException as e:
            return f"❌ Fehler beim Abrufen der Vorhersage: {str(e)}"
        except KeyError as e:
            return f"❌ Fehler beim Verarbeiten der Vorhersage: {str(e)}"


# Plugin Instance für JARVIS
def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    plugin = WeatherPlugin()
    return plugin.process(command, context)
