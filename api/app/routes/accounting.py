from fastapi import APIRouter, Request

from ..database import get_postgres_conn
from ..schemas import AccountingRequest, AccountingResponse

router = APIRouter(tags=["accounting"])


@router.post("/accounting", response_model=AccountingResponse)
async def accounting(request: Request, payload: AccountingRequest) -> AccountingResponse:
    _ = get_postgres_conn(request)
    # İskelet: radacct insert mantığı ileride eklenecek.
    return AccountingResponse(result="not_implemented", reason="Accounting write not implemented yet")

