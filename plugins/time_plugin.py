"""Time Plugin - Provides current time and date information"""
from datetime import datetime
import json

# Plugin Metadata
PLUGIN_NAME = "Zeit & Datum"
PLUGIN_DESCRIPTION = "Zeigt aktuelle Uhrzeit, Datum und Zeitzone"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "JARVIS Team"

def process(message: str) -> dict:
    """
    Process a message and return time/date information
    
    Args:
        message: User message to process
        
    Returns:
        dict with response and metadata
    """
    message_lower = message.lower()
    
    # Check if message is asking for time/date
    time_keywords = ['uhrzeit', 'zeit', 'wie spät', 'datum', 'wochentag']
    
    if any(keyword in message_lower for keyword in time_keywords):
        now = datetime.now()
        
        response = {
            'success': True,
            'response': f"Aktuelle Zeit: {now.strftime('%H:%M:%S')}\nDatum: {now.strftime('%d.%m.%Y')}\nWochentag: {now.strftime('%A')}",
            'data': {
                'time': now.strftime('%H:%M:%S'),
                'date': now.strftime('%d.%m.%Y'),
                'weekday': now.strftime('%A'),
                'timestamp': now.isoformat()
            }
        }
        return response
    
    return {
        'success': False,
        'response': None
    }


def health_check() -> dict:
    """Health-Check für das Zeit-Plugin."""
    return {
        "status": "ok",
        "missing_keys": [],
        "errors": []
    }

if __name__ == "__main__":
    # Test the plugin
    print(f"Testing {PLUGIN_NAME}...")
    test_messages = [
        "Wie spät ist es?",
        "Welches Datum haben wir?",
        "Was ist die Uhrzeit?"
    ]
    
    for msg in test_messages:
        result = process(msg)
        print(f"\nQ: {msg}")
        print(f"A: {json.dumps(result, indent=2, ensure_ascii=False)}")
