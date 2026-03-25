from fastapi import APIRouter, Request

from ..database import get_postgres_conn
from ..schemas import UserOut

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserOut])
async def users(request: Request) -> list[UserOut]:
    # İskelet: radusergroup/radcheck join sorgusu ileride eklenecek.
    _ = get_postgres_conn(request)
    return []

