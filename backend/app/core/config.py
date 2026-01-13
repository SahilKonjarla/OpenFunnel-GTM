from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Setting environment variables
    app_env: str = "dev"
    log_level: str = "INFO"

    # Database + Queue settings
    postgres_dsn: str = "postgresql+psycopg2://Sahil:app@postgres:5432/openfunnel"
    redis_url: str = "redis://localhost:6379/0"

    # LLM settings
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
