from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]  # repo root
BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FasalSaathi API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "fasalsaathi-dev-secret-key-change-me"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'fasalsaathi_app.db').as_posix()}"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    weather_default_location: str = "Itarsi, Madhya Pradesh"
    weather_default_lat: float = 22.6148
    weather_default_lon: float = 77.7622
    openweather_api_key: str | None = None
    data_gov_api_key: str | None = None
    data_gov_base_url: str = "https://api.data.gov.in/resource"
    data_gov_market_resource_id: str = "9ef84268-d588-465a-a308-a864a43d0070"
    data_gov_timeout_seconds: float = 10.0
    data_gov_default_limit: int = 100
    data_gov_filtered_limit: int = 1000
    data_gov_max_filtered_pages: int = 5

    # AI Keys
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: float = 20.0
    
    # User's AI Specifics
    gemini_chat_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "farmer-chatbot"
    pinecone_namespace: str = "agriculture-docs"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
