from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Character Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_characters"

    NVIDIA_API_KEY: str

    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
