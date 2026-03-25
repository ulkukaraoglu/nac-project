import os
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    api_env: str = Field(default="local")

    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    redis_host: str
    redis_port: int = 6379
    redis_db: int = 0

    # Auth rate limiting (Redis)
    auth_rate_max_attempts: int = Field(default=5)
    auth_rate_window_seconds: int = Field(default=60)
    auth_rate_block_seconds: int = Field(default=300)

    @classmethod
    def from_env(cls) -> "Settings":
        # NOTE: Secret'lar local'de `.env` ile gelir; burada hardcode yok.
        return cls(
            api_env=os.getenv("API_ENV", "local"),
            postgres_host=os.environ["POSTGRES_HOST"],
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.environ["POSTGRES_DB"],
            postgres_user=os.environ["POSTGRES_USER"],
            postgres_password=os.environ["POSTGRES_PASSWORD"],
            redis_host=os.environ["REDIS_HOST"],
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            auth_rate_max_attempts=int(os.getenv("AUTH_RATE_MAX_ATTEMPTS", "5")),
            auth_rate_window_seconds=int(os.getenv("AUTH_RATE_WINDOW_SECONDS", "60")),
            auth_rate_block_seconds=int(os.getenv("AUTH_RATE_BLOCK_SECONDS", "300")),
        )


def require_env(name: str) -> str:
    value: Optional[str] = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value

