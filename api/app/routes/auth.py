from fastapi import APIRouter, Request

from ..database import get_redis_client, get_postgres_conn
from ..schemas import AuthRequest, AuthResponse

router = APIRouter(tags=["auth"])


@router.post("/auth", response_model=AuthResponse)
async def auth(request: Request, payload: AuthRequest) -> AuthResponse:
    # İskelet: ileride rlm_pap/rlm_crypt ile aynı doğrulama mantığını burada bağlayacağız.
    # Şimdilik bağlantı altyapısının hazır olduğunu göstermek için dependency'leri doğruluyoruz.
    _ = get_postgres_conn(request)
    _ = get_redis_client(request)

    return AuthResponse(result="not_implemented", reason="Auth logic not implemented yet")

