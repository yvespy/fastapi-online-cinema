from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str

    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 25))
    SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME", None)
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD", None)
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@example.com")
    USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_default_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TestSettings(Settings):
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    MAIL_FROM: str = "test@example.com"
    USE_TLS: bool = False
    SECRET_KEY: str = "TEST_SECRET_KEY"


settings = Settings()
