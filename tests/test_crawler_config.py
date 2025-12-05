import os
from pathlib import Path

from services.crawler_service.config import load_config


def test_api_key_env_override(monkeypatch, tmp_path):
    cfg_file = tmp_path / "crawler.json"
    cfg_file.write_text('{"api_key": "file-key", "listen_port": 9000}', encoding="utf-8")
    monkeypatch.setenv("JARVIS_CRAWLER_API_KEY", "env-key")

    cfg = load_config(cfg_file)

    assert cfg.api_key == "env-key"
    assert cfg.listen_port == 9000


def test_api_key_stripped(monkeypatch, tmp_path):
    cfg_file = tmp_path / "crawler.json"
    cfg_file.write_text('{"api_key": "  spaced-key  "}', encoding="utf-8")
    monkeypatch.delenv("JARVIS_CRAWLER_API_KEY", raising=False)

    cfg = load_config(cfg_file)

    assert cfg.api_key == "spaced-key"
