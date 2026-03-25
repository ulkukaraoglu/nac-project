from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import Settings
from .database import get_postgres_conn, get_redis_client, init_postgres, init_redis
from .routes import build_routes
from .schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = Settings.from_env()

    # Bağlantı altyapısını "hazır" yapmak: sonraki adımlarda endpoint'ler DB/Redis'i kullanacak.
    try:
        app.state.postgres_conn = await init_postgres(cfg)
        app.state.redis_client = await init_redis(cfg)
    except Exception as exc:  # noqa: BLE001
        # Bu adımda hata yönetimini sade tutuyoruz.
        # Sağlık endpoint'leri çalışmaya devam etse bile diğer endpoint'lerde 500 dönecek.
        app.state.startup_error = str(exc)
    yield
    # Shutdown: bağlantıları kapat.
    try:
        conn = getattr(app.state, "postgres_conn", None)
        if conn is not None:
            conn.close()
    finally:
        client = getattr(app.state, "redis_client", None)
        if client is not None:
            await client.close()


app = FastAPI(title="nac-api", lifespan=lifespan)
app.include_router(build_routes())


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content=ErrorResponse(detail=str(exc)).model_dump())


@app.get("/health", response_model=dict[str, Any])
def health() -> dict[str, Any]:
    # Basit; asıl "servis ayağa kalktı" kontrolü docker healthcheck ile.
    return {"status": "ok"}


@app.get("/healthz", response_model=dict[str, Any])
def healthz() -> dict[str, Any]:
    # Mevcut compose healthcheck uyumluluğu için alias.
    return {"status": "ok"}

