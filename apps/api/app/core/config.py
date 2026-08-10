from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "development-secret-change-me"
MIN_PRODUCTION_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "WhatsFlow AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/whatsflow"
    )

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_GRAPH_API_VERSION: str = "v23.0"
    META_WEBHOOK_VERIFY_TOKEN: str = ""
    META_WEBHOOK_APP_SECRET: str = ""
    META_EMBEDDED_SIGNUP_CONFIG_ID: str = ""
    META_REDIRECT_URI: str = ""

    ENCRYPTION_KEY: str = ""

    OPENAI_API_KEY: str = ""

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "whatsflow"

    CORS_ORIGINS: str = "http://localhost:3000"

    ENABLE_API_DOCS: bool = True

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if not self.is_production:
            return self

        if len(self.JWT_SECRET) < MIN_PRODUCTION_SECRET_LENGTH:
            raise ValueError(
                "JWT_SECRET must be at least "
                f"{MIN_PRODUCTION_SECRET_LENGTH} characters in production."
            )

        if self.JWT_SECRET == DEFAULT_JWT_SECRET:
            raise ValueError(
                "Default JWT_SECRET cannot be used in production."
            )

        if not self.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY must be set in production."
            )

        if not self.CORS_ORIGINS:
            raise ValueError(
                "CORS_ORIGINS must be configured in production."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
