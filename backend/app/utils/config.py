from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"

    gemini_api_key: str = ""

    database_url: str = "postgresql://cloudsense:cloudsense@localhost:5432/cloudsense"

    slack_webhook_url: str = ""
    slack_alert_channel: str = "#cloud-costs"

    cost_alert_threshold: float = 100.0
    environment: str = "development"
    log_level: str = "INFO"

    # Observability
    otlp_endpoint: str = "http://localhost:4317"
    tracing_enabled: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
