from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Korean Vocab API"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "postgresql+psycopg://korean_vocab:local_dev_password@localhost:5433/korean_vocab"
    secret_key: SecretStr = SecretStr("local-development-only-secret-change-before-deploying")
    auth_token_expire_minutes: int = Field(default=60, gt=0)
    auth_cookie_secure: bool = False


settings = Settings()