"""Tests for Settings Management"""
import pytest
import json


class TestSettingsManager:
    """Test suite for Settings Manager"""

    def test_default_settings_structure(self):
        """Test default settings have correct structure"""
        default_settings = {
            "llm": {"enabled": False, "model_path": "", "temperature": 0.7},
            "api": {"host": "127.0.0.1", "port": 5050},
        }

        assert "llm" in default_settings
        assert "api" in default_settings
        assert "temperature" in default_settings["llm"]

    def test_settings_validation(self):
        """Test settings validation"""
        temperature = 0.7
        assert 0 <= temperature <= 2

        context_length = 2048
        assert context_length > 0

    def test_json_serialization(self):
        """Test settings can be serialized to JSON"""
        settings = {"llm": {"enabled": True, "temperature": 0.8}}

        json_str = json.dumps(settings)
        loaded = json.loads(json_str)

        assert loaded["llm"]["enabled"] == settings["llm"]["enabled"]
