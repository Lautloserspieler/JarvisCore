"""Calculator Plugin - Performs basic math calculations"""
import re

# Plugin Metadata
PLUGIN_NAME = "Taschenrechner"
PLUGIN_DESCRIPTION = "Führt einfache mathematische Berechnungen aus"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "JARVIS Team"

def process(message: str) -> dict:
    """
    Process a message and perform calculations
    
    Args:
        message: User message to process
        
    Returns:
        dict with response and metadata
    """
    message_lower = message.lower()
    
    # Check for calculation keywords
    calc_keywords = ['rechne', 'berechne', 'was ist', 'ergebnis von']
    
    if any(keyword in message_lower for keyword in calc_keywords):
        # Extract mathematical expression
        # Support: 5+3, 10-2, 4*6, 20/5, 2**3 (power)
        pattern = r'([0-9\.]+)\s*([+\-*/]|\*\*)\s*([0-9\.]+)'
        match = re.search(pattern, message)
        
        if match:
            try:
                num1 = float(match.group(1))
                operator = match.group(2)
                num2 = float(match.group(3))
                
                # Perform calculation
                if operator == '+':
                    result = num1 + num2
                elif operator == '-':
                    result = num1 - num2
                elif operator == '*':
                    result = num1 * num2
                elif operator == '/':
                    if num2 == 0:
                        return {
                            'success': False,
                            'response': 'Fehler: Division durch Null ist nicht möglich'
                        }
                    result = num1 / num2
                elif operator == '**':
                    result = num1 ** num2
                else:
                    return {'success': False, 'response': None}
                
                return {
                    'success': True,
                    'response': f"{num1} {operator} {num2} = {result}",
                    'data': {
                        'expression': f"{num1} {operator} {num2}",
                        'result': result
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'response': f'Fehler bei der Berechnung: {str(e)}'
                }
    
    return {
        'success': False,
        'response': None
    }


def health_check() -> dict:
    """Health-Check für das Taschenrechner-Plugin."""
    return {
        "status": "ok",
        "missing_keys": [],
        "errors": []
    }

if __name__ == "__main__":
    # Test the plugin
    print(f"Testing {PLUGIN_NAME}...")
    test_messages = [
        "Rechne 5 + 3",
        "Was ist 10 * 7?",
        "Berechne 100 / 4",
        "Was ist 2 ** 8"
    ]
    
    for msg in test_messages:
        result = process(msg)
        print(f"\nQ: {msg}")
        if result['success']:
            print(f"A: {result['response']}")
        else:
            print("A: Keine Berechnung gefunden")
