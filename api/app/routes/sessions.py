from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Query

from ..database import get_postgres_conn
from ..schemas import SessionOut

router = APIRouter(tags=["sessions"])


@router.get("/sessions/active", response_model=list[SessionOut])
async def active_sessions(
    request: Request,
    username: Optional[str] = Query(default=None),
) -> list[SessionOut]:
    # İskelet: radacct içinden "aktif" session sorgusu (start/stop) ileride eklenecek.
    _ = get_postgres_conn(request)

    # DB şeması hazır; bu adımda sadece endpointin dönmesini garanti ediyoruz.
    _ = username
    return []

