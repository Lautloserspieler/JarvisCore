import pytest
from fastapi import HTTPException

from services.crawler_service import main


def test_verify_api_key_skips_when_not_configured(monkeypatch):
    monkeypatch.setattr(main.CONFIG, "api_key", "")
    # Should not raise when no API key is configured
    main.verify_api_key(None)
    main.verify_api_key("anything")


def test_verify_api_key_enforces_configured_key(monkeypatch):
    monkeypatch.setattr(main.CONFIG, "api_key", "secret-token")
    with pytest.raises(HTTPException) as excinfo_missing:
        main.verify_api_key(None)
    assert excinfo_missing.value.status_code == 401

    with pytest.raises(HTTPException) as excinfo_wrong:
        main.verify_api_key("wrong")
    assert excinfo_wrong.value.status_code == 401

    # Correct key should pass without raising
    main.verify_api_key("secret-token")
