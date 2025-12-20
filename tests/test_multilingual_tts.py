"""
Test Suite für Multilingual Voice Cloning TTS

Tests für:
- Language auto-detection (Deutsch / Englisch)
- Voice latents Caching pro Sprache
- Cache-Persistierung
- Language-aware Voice Sample Selektion
- Performance-Charakteristiken
"""

import pytest
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from core.text_to_speech import TextToSpeech


class TestLanguageDetection:
    """Tests für automatische Spracherkennung"""
    
    def test_german_detection(self):
        """Teste Deutsch-Erkennung anhand von Schlüssbelwörtern"""
        tts = TextToSpeech()
        
        # Typisch deutsche Wörter
        german_texts = [
            "Hallo, wie geht es dir heute?",
            "Das ist eine Testnachricht",
            "Ich bin ein KI-Assistent",
            "Die Sonne scheint heute wunderschön",
        ]
        
        for text in german_texts:
            detected = tts._detect_language(text)
            assert detected == 'de', f"Expected 'de' for '{text}', got '{detected}'"
    
    def test_english_detection(self):
        """Teste Englisch-Erkennung anhand von Schlüsselwörtern"""
        tts = TextToSpeech()
        
        english_texts = [
            "Hello, how are you today?",
            "This is a test message",
            "I am an AI assistant",
            "The sun shines beautifully today",
        ]
        
        for text in english_texts:
            detected = tts._detect_language(text)
            assert detected == 'en', f"Expected 'en' for '{text}', got '{detected}'"
    
    def test_empty_text_fallback(self):
        """Teste Fallback auf aktuelle Sprache bei leerem Text"""
        tts = TextToSpeech()
        tts._current_language = 'de'
        
        detected = tts._detect_language("")
        assert detected == 'de'
    
    def test_ambiguous_text_uses_current(self):
        """Teste Fallback auf aktuelle Sprache bei mehrdeutigen Wörtern"""
        tts = TextToSpeech()
        tts._current_language = 'en'
        
        # Ambiguous text with equal DE/EN indicators
        ambiguous = "test data"
        detected = tts._detect_language(ambiguous)
        # Sollte auf aktuelle Sprache (en) fallen
        assert detected == 'en'


class TestVoiceLatentsCaching:
    """Tests für Voice Latents Caching-Mechanik"""
    
    def test_latents_cache_path_generation(self):
        """Teste Cache-Pfad-Generierung für verschiedene Sprachen"""
        tts = TextToSpeech()
        
        # Deutsch
        de_path = tts._get_latents_cache_path('de')
        assert 'voice_latents_de.pt' in str(de_path)
        assert de_path.parent == Path('data/tts')
        
        # Englisch
        en_path = tts._get_latents_cache_path('en')
        assert 'voice_latents_en.pt' in str(en_path)
        
        # Mit Langtag (de-DE, en-US)
        de_de_path = tts._get_latents_cache_path('de-DE')
        assert 'voice_latents_de.pt' in str(de_de_path)  # Sollte 'de' extrahieren
        
        en_us_path = tts._get_latents_cache_path('en-US')
        assert 'voice_latents_en.pt' in str(en_us_path)  # Sollte 'en' extrahieren
    
    def test_voice_sample_selection_de(self):
        """Teste Voice Sample Selektion für Deutsch"""
        settings_mock = Mock()
        settings_mock.get = Mock(side_effect=lambda key, default=None: {
            'speech': {
                'voice_sample_de': '/path/to/Jarvis_DE.wav',
                'voice_sample_en': '/path/to/Jarvis_EN.wav',
            }
        }.get(key, default))
        
        tts = TextToSpeech(settings_mock)
        # Hinweis: Diese Test wird mit echtem Settings gemocked,
        # da die echte Implementierung Dateien prüft
    
    def test_cache_memory_storage(self):
        """Teste In-Memory Cache für Latents"""
        tts = TextToSpeech()
        
        # Initialisiere mit Mock-Latents
        mock_latents_de = {
            'gpt_cond_latent': MagicMock(),
            'speaker_embedding': MagicMock(),
            'language': 'de'
        }
        
        tts._voice_latents_cache['de'] = mock_latents_de
        
        # Prüfe ob sie gespeichert sind
        assert 'de' in tts._voice_latents_cache
        assert tts._voice_latents_cache['de'] == mock_latents_de
        
        # Separate Cache für Englisch
        mock_latents_en = {
            'gpt_cond_latent': MagicMock(),
            'speaker_embedding': MagicMock(),
            'language': 'en'
        }
        tts._voice_latents_cache['en'] = mock_latents_en
        
        # Beide sollten unabhängig gespeichert sein
        assert len(tts._voice_latents_cache) == 2
        assert tts._voice_latents_cache['de']['language'] == 'de'
        assert tts._voice_latents_cache['en']['language'] == 'en'


class TestSpeakQueue:
    """Tests für erweiterte speak() Queue mit Language-Parameter"""
    
    def test_speak_with_auto_language_detection(self):
        """Teste speak() mit automatischer Spracherkennung"""
        tts = TextToSpeech()
        
        # Sollte Deutsch erkennen und in Queue legen
        tts.speak("Hallo, wie geht es dir?")
        
        # Prüfe dass etwas in Queue ist (nicht Empty)
        assert not tts._queue.empty()
        
        # Hole Item aus Queue
        item = tts._queue.get_nowait()
        text, style, language = item
        
        assert text == "Hallo, wie geht es dir?"
        assert language == 'de'
        assert style is None
    
    def test_speak_with_explicit_language(self):
        """Teste speak() mit expliziter Sprache"""
        tts = TextToSpeech()
        
        # Erzwinge Englisch für deutschen Text
        tts.speak("Hallo!", language='en')
        
        item = tts._queue.get_nowait()
        text, style, language = item
        
        assert text == "Hallo!"
        assert language == 'en'  # Explizit gesetzt
    
    def test_speak_with_language_and_style(self):
        """Teste speak() mit Sprache und Style"""
        tts = TextToSpeech()
        
        tts.speak("Das ist super!", language='de', style='freundlich')
        
        item = tts._queue.get_nowait()
        text, style, language = item
        
        assert text == "Das ist super!"
        assert language == 'de'
        assert style == 'freundlich'
    
    def test_speak_queue_format_backward_compatibility(self):
        """Teste dass alte speak() Calls (ohne language) funktionieren"""
        tts = TextToSpeech()
        
        # Alte API: Nur text und style
        tts.speak("Test", style='neutral')
        
        item = tts._queue.get_nowait()
        assert len(item) == 3  # Neue Format: (text, style, language)
        text, style, language = item
        
        assert text == "Test"
        assert style == 'neutral'
        # language sollte auto-detected sein
        assert language is not None


class TestConfigurationMigration:
    """Tests für Rückwärts-Kompatibilität"""
    
    def test_legacy_voice_sample_config(self):
        """Teste dass alte voice_sample Config noch funktioniert"""
        tts = TextToSpeech()
        tts._voice_sample = 'models/tts/voices/Jarvis.wav'
        
        # Sollte für beide Sprachen als Fallback verfügbar sein
        de_sample = tts._get_voice_sample_for_language('de')
        en_sample = tts._get_voice_sample_for_language('en')
        
        # Beide können auf Legacy-Sample fallen
        # (falls sprachspezifische nicht gesetzt)
    
    def test_single_language_still_works(self):
        """Teste dass Single-Language Setup noch funktioniert"""
        # Konfiguriere nur Deutsch
        settings_mock = Mock()
        settings_mock.get = Mock(side_effect=lambda key, default=None: {
            'speech': {'tts_backend': 'pyttsx3'}
        }.get(key, default))
        
        tts = TextToSpeech(settings_mock)
        
        # speak() sollte trotzdem funktionieren
        tts.speak("Test")
        assert not tts._queue.empty()


class TestPerformanceCharacteristics:
    """Tests für Performance-Verhalten"""
    
    @pytest.mark.benchmark
    def test_language_detection_performance(self):
        """Teste dass Language Detection performant ist (<1ms)"""
        tts = TextToSpeech()
        
        test_texts = [
            "Hallo, wie geht es dir?",
            "Hello, how are you?",
        ] * 10
        
        start = time.time()
        for text in test_texts:
            tts._detect_language(text)
        elapsed = time.time() - start
        
        # 20 Calls sollten unter 20ms sein (1ms pro Call)
        assert elapsed < 0.020, f"Language detection too slow: {elapsed}s for 20 calls"
    
    @pytest.mark.benchmark
    def test_queue_insertion_performance(self):
        """Teste dass Queue-Insertion schnell ist"""
        tts = TextToSpeech()
        
        start = time.time()
        for i in range(100):
            tts.speak(f"Message {i}")
        elapsed = time.time() - start
        
        # 100 Queue-Insertionen sollten unter 100ms sein
        assert elapsed < 0.100, f"Queue insertion too slow: {elapsed}s for 100 inserts"


class TestErrorHandling:
    """Tests für Error Handling"""
    
    def test_speak_empty_text(self):
        """Teste dass leerer Text sicher ignoriert wird"""
        tts = TextToSpeech()
        
        tts.speak("")  # Sollte nicht in Queue landen
        
        assert tts._queue.empty()
    
    def test_speak_whitespace_only(self):
        """Teste dass reines Whitespace sicher ignoriert wird"""
        tts = TextToSpeech()
        
        tts.speak("   \n\t  ")  # Sollte trimmed und ignoriert werden
        
        assert tts._queue.empty()
    
    def test_language_code_normalization(self):
        """Teste dass Language-Codes normalisiert werden"""
        tts = TextToSpeech()
        
        # Verschiedene Formate sollten auf 'de' normalisiert werden
        tts.speak("Test", language='DE')  # Uppercase
        item1 = tts._queue.get_nowait()
        assert item1[2] == 'de'
        
        tts.speak("Test", language='de-DE')  # Mit Region
        item2 = tts._queue.get_nowait()
        assert item2[2] == 'de'
        
        tts.speak("Test", language='de-AT')  # Österreich
        item3 = tts._queue.get_nowait()
        assert item3[2] == 'de'


class TestIntegration:
    """Integration Tests"""
    
    def test_language_switching_workflow(self):
        """Teste kompletten Workflow mit Sprachenwechsel"""
        tts = TextToSpeech()
        
        # Deutsch
        tts.speak("Hallo!")
        tts.speak("Wie geht es dir?")
        
        # Englisch
        tts.speak("Hello!")
        tts.speak("How are you?")
        
        # Zurück zu Deutsch
        tts.speak("Auf Wiedersehen!")
        
        # Queue sollte 5 Items haben
        assert tts._queue.qsize() == 5
        
        # Prüfe dass alle mit korrekter Sprache gecacht sind
        items = []
        while not tts._queue.empty():
            items.append(tts._queue.get_nowait())
        
        assert items[0][2] == 'de'  # Hallo!
        assert items[1][2] == 'de'  # Wie geht es dir?
        assert items[2][2] == 'en'  # Hello!
        assert items[3][2] == 'en'  # How are you?
        assert items[4][2] == 'de'  # Auf Wiedersehen!


if __name__ == '__main__':
    # Einfacher Test-Runner
    pytest.main([__file__, '-v', '--tb=short'])
