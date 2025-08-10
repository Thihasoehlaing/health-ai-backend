# app/config.py
from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    PG_CONNECTION: str = "postgresql+psycopg"
    PG_HOST: str = "127.0.0.1"
    PG_PORT: int = 5432
    PG_DATABASE: str = "hospital"
    PG_USERNAME: str = "postgres"
    PG_PASSWORD: str = "secret"

    # MongoDB
    MONGO_CONNECTION: str = "mongodb"  # e.g., mongodb or mongodb+srv
    MONGO_HOST: str = "127.0.0.1"
    MONGO_PORT: int = 27017
    MONGO_DATABASE: str = "hospital"
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_AUTHSOURCE: str = "admin"  # common default when using auth

    # App
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    JWT_SECRET: str = "change-me"
    JWT_EXPIRES_MIN: int = 60

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    CORS_ORIGINS_CSV: Optional[str] = None  # allow comma-separated origins in .env

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def postgres_url(self) -> str:
        user = quote_plus(self.PG_USERNAME)
        pwd = quote_plus(self.PG_PASSWORD)
        return f"{self.PG_CONNECTION}://{user}:{pwd}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"

    @property
    def mongo_url(self) -> str:
        # Support both mongodb://host:port and mongodb+srv://host
        # Include credentials only if provided
        auth = ""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            auth = f"{quote_plus(self.MONGO_USERNAME)}:{quote_plus(self.MONGO_PASSWORD)}@"

        if self.MONGO_CONNECTION.endswith("+srv"):
            # SRV URIs don't use port in the URL
            base = f"{self.MONGO_CONNECTION}://{auth}{self.MONGO_HOST}"
            return f"{base}/?authSource={self.MONGO_AUTHSOURCE}"
        else:
            base = f"{self.MONGO_CONNECTION}://{auth}{self.MONGO_HOST}:{self.MONGO_PORT}"
            return f"{base}/?authSource={self.MONGO_AUTHSOURCE}"

    def cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS:
            return [str(x) for x in self.CORS_ORIGINS]
        if self.CORS_ORIGINS_CSV:
            return [x.strip() for x in self.CORS_ORIGINS_CSV.split(",") if x.strip()]
        return []


settings = Settings()
