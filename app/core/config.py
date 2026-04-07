from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "store-email-ops"
    environment: str = "local"
    database_url: str = "sqlite:///./local.db"
    message_bus_backend: str = "memory"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "campaign-send-requests"
    sqs_queue_url: str = ""
    internal_api_token: str = "dev-internal-token"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
