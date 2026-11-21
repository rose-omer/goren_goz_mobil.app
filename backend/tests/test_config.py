"""Ayar ayrıştırma testleri (plan Y1)."""

from __future__ import annotations

from core.config import Settings


def test_env_values_parse(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test, http://b.test")
    monkeypatch.setenv("RATE_LIMIT", "3")
    monkeypatch.setenv("VLM_MODEL", "gemma-4-e2b")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
    assert settings.rate_limit_per_minute == 3
    assert settings.vlm_model == "gemma-4-e2b"


def test_new_rate_limit_name_wins(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "42")
    assert Settings(_env_file=None).rate_limit_per_minute == 42


def test_secure_defaults():
    settings = Settings(_env_file=None)
    assert settings.debug is False
    assert settings.port == 8110
    assert settings.host == "127.0.0.1"
    assert settings.cors_origins == []


def test_yaml_values_are_loaded():
    # config.yaml: lower_after_frames = 5
    assert Settings(_env_file=None).lower_after_frames == 5
