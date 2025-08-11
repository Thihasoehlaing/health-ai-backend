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
    MONGO_CONNECTION: str = "mongodb"  # e.g. mongodb or mongodb+srv
    MONGO_HOST: str = "127.0.0.1"
    MONGO_PORT: int = 27017
    MONGO_DATABASE: str = "hospital"
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_AUTHSOURCE: Optional[str] = "admin"  # set to the DB where the user was created

    # App
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    JWT_SECRET: str  # provide via .env
    JWT_EXPIRES_MIN: int = 60

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []  # JSON list in .env, e.g. ["http://localhost:5173"]
    CORS_ORIGINS_CSV: Optional[str] = None  # or CSV: http://localhost:5173,http://127.0.0.1:5173

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def postgres_url(self) -> str:
        user = quote_plus(self.PG_USERNAME)
        pwd = quote_plus(self.PG_PASSWORD)
        return f"{self.PG_CONNECTION}://{user}:{pwd}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"

    @property
    def mongo_url(self) -> str:
        """
        Builds a Mongo URL that works for both mongodb:// and mongodb+srv://
        Includes auth only when username/password are provided.
        Appends ?authSource=... when auth is used.
        """
        auth = ""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            auth = f"{quote_plus(self.MONGO_USERNAME)}:{quote_plus(self.MONGO_PASSWORD)}@"

        if self.MONGO_CONNECTION.endswith("+srv"):
            base = f"{self.MONGO_CONNECTION}://{auth}{self.MONGO_HOST}"
            if auth:
                return f"{base}/?authSource={self.MONGO_AUTHSOURCE or 'admin'}"
            return f"{base}/"
        else:
            base = f"{self.MONGO_CONNECTION}://{auth}{self.MONGO_HOST}:{self.MONGO_PORT}"
            if auth:
                return f"{base}/?authSource={self.MONGO_AUTHSOURCE or 'admin'}"
            return f"{base}/"

    def cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS:
            return [str(x) for x in self.CORS_ORIGINS]
        if self.CORS_ORIGINS_CSV:
            return [o.strip() for o in self.CORS_ORIGINS_CSV.split(",") if o.strip()]
        return []

    def is_prod(self) -> bool:
        return self.APP_ENV.lower() in {"prod", "production"}


settings = Settings()
