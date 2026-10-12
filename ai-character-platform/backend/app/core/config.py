from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Character Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_characters"

    NVIDIA_API_KEY: str
    NVIDIA_MODEL: str = "meta/llama-3.2-11b-vision-instruct"

    POLLINATIONS_API_KEY: str = ""
    STABLE_HORDE_API_KEY: str = "0000000000"
    METRICS_LOG_PATH: str = "logs/generation_metrics.jsonl"

    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
