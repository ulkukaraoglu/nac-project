import anyio
import psycopg
import redis.asyncio as redis_asyncio
from urllib.parse import quote_plus

from .config import Settings


def _postgres_dsn(cfg: Settings) -> str:
    # Password URL-encoding gerekebilir (örn. özel karakterler).
    user = quote_plus(cfg.postgres_user)
    password = quote_plus(cfg.postgres_password)
    host = cfg.postgres_host
    port = cfg.postgres_port
    db = cfg.postgres_db
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _redis_url(cfg: Settings) -> str:
    return f"redis://{cfg.redis_host}:{cfg.redis_port}/{cfg.redis_db}"


async def init_redis(cfg: Settings) -> redis_asyncio.Redis:
    client = redis_asyncio.from_url(_redis_url(cfg), decode_responses=True)
    # Basit canlılık doğrulaması
    await client.ping()
    return client


async def init_postgres(cfg: Settings) -> psycopg.Connection:
    dsn = _postgres_dsn(cfg)
    # Startup sırasında bağlantıyı test etmek için sync connect yapıyoruz.
    conn = await anyio.to_thread.run_sync(lambda: psycopg.connect(dsn, connect_timeout=5))
    return conn


def get_postgres_conn(request) -> psycopg.Connection:
    conn = getattr(request.app.state, "postgres_conn", None)
    if conn is None:
        raise RuntimeError("Postgres bağlantısı henüz hazır değil")
    return conn


def get_redis_client(request) -> redis_asyncio.Redis:
    client = getattr(request.app.state, "redis_client", None)
    if client is None:
        raise RuntimeError("Redis bağlantısı henüz hazır değil")
    return client

