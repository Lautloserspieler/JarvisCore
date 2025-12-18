"""Pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return {
        "llm": {
            "enabled": True,
            "model_path": "test_model.gguf",
            "context_length": 2048,
            "temperature": 0.7,
            "max_tokens": 512
        },
        "api": {
            "host": "127.0.0.1",
            "port": 5050
        }
    }

@pytest.fixture
def mock_plugin_config():
    """Mock plugin configuration"""
    return {
        "id": "test_plugin",
        "name": "Test Plugin",
        "description": "A test plugin",
        "version": "1.0.0",
        "author": "Test Author",
        "enabled": False,
        "requires_api_key": False
    }
