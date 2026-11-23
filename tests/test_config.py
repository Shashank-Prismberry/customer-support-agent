import pytest
from pydantic import ValidationError

from support_agent.core.config import Settings


def test_settings_load_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "test-support-agent")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")

    config = Settings(_env_file=None)

    assert config.app_name == "test-support-agent"
    assert config.app_env == "test"
    assert config.app_port == 9000
    assert config.jwt_secret_key is not None
    assert config.jwt_secret_key.get_secret_value() == "test-secret"
    assert config.llm_api_key is not None
    assert config.llm_api_key.get_secret_value() == "test-api-key"


def test_settings_reject_invalid_port(monkeypatch):
    monkeypatch.setenv("APP_PORT", "70000")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
