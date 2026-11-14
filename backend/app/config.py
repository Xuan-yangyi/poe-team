from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "IDH Platform"
    debug: bool = False

    # Database
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "idh_crm"
    db_user: str = "idh_app"
    db_password: str = "idh_dev"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 24

    # Redis (fakeredis in dev)
    redis_url: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
