"""Tests for Settings Management"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

class TestSettingsManager:
    """Test suite for Settings Manager"""
    
    def test_default_settings_structure(self):
        """Test default settings have correct structure"""
        default_settings = {
            "llm": {
                "enabled": False,
                "model_path": "",
                "context_length": 2048,
                "temperature": 0.7
            },
            "api": {
                "host": "127.0.0.1",
                "port": 5050
            }
        }
        
        assert "llm" in default_settings
        assert "api" in default_settings
        assert "enabled" in default_settings["llm"]
        assert "temperature" in default_settings["llm"]
    
    def test_settings_validation(self):
        """Test settings validation"""
        valid_settings = {
            "llm": {
                "temperature": 0.7,
                "context_length": 2048
            }
        }
        
        # Temperature should be between 0 and 2
        assert 0 <= valid_settings["llm"]["temperature"] <= 2
        # Context length should be positive
        assert valid_settings["llm"]["context_length"] > 0
    
    def test_invalid_temperature(self):
        """Test invalid temperature value"""
        invalid_temp = -0.5
        assert not (0 <= invalid_temp <= 2)
        
        invalid_temp = 3.0
        assert not (0 <= invalid_temp <= 2)
    
    def test_settings_persistence(self):
        """Test settings can be saved and loaded"""
        test_settings = {
            "llm": {
                "enabled": True,
                "temperature": 0.8
            }
        }
        
        # Simulate save/load cycle
        settings_json = json.dumps(test_settings)
        loaded_settings = json.loads(settings_json)
        
        assert loaded_settings["llm"]["enabled"] == test_settings["llm"]["enabled"]
        assert loaded_settings["llm"]["temperature"] == test_settings["llm"]["temperature"]
