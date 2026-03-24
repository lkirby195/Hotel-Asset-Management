from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hotel_am"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/hotel_am"
    redis_url: str = "redis://localhost:6379/0"

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwks_url: str = "https://frank-monkfish-9.clerk.accounts.dev/.well-known/jwks.json"

    profitsword_base_url: str = "https://ksl.profitsage.net/PS-Handlers"
    profitsword_username: str = ""
    profitsword_password: str = ""
    profitsword_dataset_actuals: int = -3
    profitsword_dataset_budget: int = 2
    profitsword_dataset_forecast: int = 1

    dev_auth_bypass: bool = False
    frontend_url: str = ""

    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
