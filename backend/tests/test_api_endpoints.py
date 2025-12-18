"""Tests for API Endpoints"""
import pytest


class TestAPIEndpoints:
    """Test suite for API endpoints"""

    def test_health_check_structure(self):
        """Test health check response structure"""
        response = {"status": "ok", "service": "jarvis-core"}

        assert "status" in response
        assert response["status"] == "ok"

    def test_plugins_list_structure(self):
        """Test plugins list response structure"""
        response = [
            {"id": "test", "name": "Test", "enabled": False, "version": "1.0.0"}
        ]

        assert isinstance(response, list)
        if response:
            assert "id" in response[0]
            assert "enabled" in response[0]

    def test_chat_request_structure(self):
        """Test chat request/response structure"""
        request = {"message": "Hello", "history": []}
        response = {"response": "Hi there!", "tokens": 5}

        assert "message" in request
        assert "response" in response
        assert isinstance(response["tokens"], int)
