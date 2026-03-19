from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="mind-alcove-ai-backend")
    env: str = Field(default="development")
    debug: bool = Field(default=False)

    # Database
    db_host: str = Field(default="localhost")
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # Cache
    cache_type: str = Field(default="memory")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = 6379
    redis_db: int = 0

    # Google GenAI
    google_api_key: str

    # Security
    secret_key: str
    s2s_token_ttl: int = 300

    # Langsmith
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = "your_langsmith_api_key"
    langsmith_project: str = "Default"

    # Laravel service
    activity_list_endpoint: str = 'https://mindalcove.yourcloudnetwork.net/storage/ai-sync/ai-sync.json'

    # Logging
    log_dir: str = Field(default="logs")
    log_rotation: str = Field(default="00:00")
    log_retention: str = Field(default="15 days")
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
