"""Core Configuration Settings for Network Control Plane"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Network Control Plane"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "network-control-plane-secret-key-32bytes-long="
    AGENT_API_TOKEN: str | None = None

    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "network_control_plane"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Ollama Local LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Enterprise Okta SSO Settings
    OKTA_ISSUER_URL: str = "https://dev-12345.okta.com/oauth2/default"
    OKTA_CLIENT_ID: str = "ncp-okta-client"
    OKTA_CLIENT_SECRET: str = "okta-secret"
    OKTA_ROLE_CLAIM: str = "roles"

    # System Root Superadmin Protection Settings
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@network-control-plane.local"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
