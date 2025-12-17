"""System Info Plugin - Provides system information"""
import platform
import os

# Plugin Metadata
PLUGIN_NAME = "System Info"
PLUGIN_DESCRIPTION = "Zeigt Systeminformationen über OS, CPU, Python"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "JARVIS Team"

def process(message: str) -> dict:
    """
    Process a message and return system information
    
    Args:
        message: User message to process
        
    Returns:
        dict with response and metadata
    """
    message_lower = message.lower()
    
    # Check for system info keywords
    system_keywords = ['system', 'betriebssystem', 'os', 'python version', 'cpu', 'prozessor']
    
    if any(keyword in message_lower for keyword in system_keywords):
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': platform.node()
        }
        
        response_text = f"""System Information:
• Betriebssystem: {info['os']} {info['os_release']}
• Architektur: {info['machine']}
• Prozessor: {info['processor']}
• Python Version: {info['python_version']}
• Hostname: {info['hostname']}"""
        
        return {
            'success': True,
            'response': response_text,
            'data': info
        }
    
    return {
        'success': False,
        'response': None
    }

if __name__ == "__main__":
    # Test the plugin
    print(f"Testing {PLUGIN_NAME}...")
    test_messages = [
        "Zeige Systeminformationen",
        "Welches Betriebssystem?",
        "Python Version?"
    ]
    
    for msg in test_messages:
        result = process(msg)
        print(f"\nQ: {msg}")
        if result['success']:
            print(f"A:\n{result['response']}")
        else:
            print("A: Keine System-Info Anfrage")
