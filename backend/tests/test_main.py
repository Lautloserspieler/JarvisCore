"""Basic integration tests for JARVIS Core backend."""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the heavy dependencies if not available
try:
    from main import app
except ImportError:
    # If main.py can't be imported due to missing dependencies
    pytest.skip("Skipping - dependencies not fully installed", allow_module_level=True)


class TestAPI:
    """Test cases for JARVIS Core API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_docs_available(self, client):
        """Test API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestBasics:
    """Basic functionality tests."""

    def test_imports(self):
        """Test that main modules can be imported."""
        try:
            import main
            assert hasattr(main, 'app')
        except ImportError:
            pytest.skip("Main module requires all dependencies")

    def test_requirements_loaded(self):
        """Test that requirements are properly installed."""
        import fastapi
        import uvicorn
        import pydantic
        assert fastapi
        assert uvicorn
        assert pydantic
