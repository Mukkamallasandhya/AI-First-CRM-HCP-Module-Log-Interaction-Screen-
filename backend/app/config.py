from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env"""

    groq_api_key: str = ""
    groq_model: str = "gemma2-9b-it"
    groq_model_large: str = "llama-3.3-70b-versatile"

    database_url: str = "sqlite:///./hcp_crm.db"  # safe local fallback
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
