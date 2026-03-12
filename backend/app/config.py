from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hotel_am"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/hotel_am"
    redis_url: str = "redis://localhost:6379/0"

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwks_url: str = "https://api.clerk.com/v1/jwks"

    profitsword_api_url: str = ""
    profitsword_api_key: str = ""

    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
