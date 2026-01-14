from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Setting environment variables
    app_env: str = "dev"
    log_level: str = "INFO"

    # Database + Queue settings
    postgres_dsn: str = "postgresql+psycopg2://Sahil:app@postgres:5432/openfunnel"
    redis_url: str = "redis://redis:6379/0"

    # LLM settings
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "gemma3:1b"

    # Queue settings
    visibility_timeout_sec: int = 60
    max_attempts: int = 8

    #Scraping settings
    greenhouse_board: str = "stripe"
    lever_company: str = "netflix"

    seed_job_limit: int = 5
    http_timeout_sec: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
