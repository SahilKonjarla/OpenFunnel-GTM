from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Setting environment variables
    app_env: str = "dev"
    log_level: str = "INFO"

    # Database + Queue settings
    postgres_dsn: str = "postgresql+psycopg2://Sahil:app@postgres:5432/openfunnel"
    redis_url: str = "redis://redis:6379/0"

    # LLM settings
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "gemma3:4b"

    # Queue settings
    visibility_timeout_sec: int = 60
    max_attempts: int = 8

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
