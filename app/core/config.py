from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="mind-alcove-ai-backend")
    env: str = Field(default="development")
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # Database
    db_host: str = Field(default="localhost")
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = 6379
    redis_db: int = 0

    # Google GenAI
    google_api_key: str

    # Security
    secret_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
