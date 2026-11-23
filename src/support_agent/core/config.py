from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "customer-support-agent"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8003, ge=1, le=65535)

    jwt_secret_key: SecretStr | None = None
    jwt_issuer: str = "support-ai-backend"
    jwt_audience: str = "support-ai-services"

    llm_provider: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None

    mcp_server_url: str | None = None
    rag_service_url: str | None = None
    backend_api_url: str | None = None
    checkpoint_database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
