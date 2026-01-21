from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    postgres_dsn: str = "postgresql+psycopg2://app:app@localhost:5432/openfunnel"
    redis_url: str = "redis://localhost:6379/0"

    log_level: str = "INFO"
    visibility_timeout_sec: int = 300

    scrape_concurrency: int = 8
    raw_store_dir: str = "./data/raw"

    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model_small: str = "gemma3:4b"
    openai_api_key: str | None = os.environ.get("OPENAI_API_KEY")
    anthropic_api_key: str | None = None
    high_tier_provider: str = "openai"
    high_tier_model: str = "gpt-4o-mini"

    extract_concurrency: int = 8
    extract_batch_size: int = 32

settings = Settings()
