from fastapi import APIRouter, Request

from ..database import get_postgres_conn, get_redis_client
from ..schemas import AuthorizeRequest, AuthorizeResponse

router = APIRouter(tags=["authorize"])


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize(request: Request, payload: AuthorizeRequest) -> AuthorizeResponse:
    # İskelet: grup -> VLAN/policy mapping radgroupreply üzerinden dönecek.
    _ = get_postgres_conn(request)
    _ = get_redis_client(request)

    return AuthorizeResponse(result="not_implemented", vlan_id=None, policy_name=None)

