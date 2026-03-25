import bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..database import get_redis_client, get_postgres_conn
from ..schemas import AuthRequest

router = APIRouter(tags=["auth"])


@router.post("/auth")
async def auth(request: Request, payload: AuthRequest):
    """
    PAP authentication (rlm_rest entegrasyonu için).

    FreeRADIUS, rlm_rest çağrısında HTTP status'a göre accept/reject yapacak şekilde kurgulanmıştır.
    - 200: accepted
    - 401/403: rejected (veya inactive)

    Response JSON'unda FreeRADIUS tarafından işlenebilmesi için
    `reply:` prefix'i kullandık.
    """
    # Bağlantı altyapısı hazır mı?
    conn = get_postgres_conn(request)
    _ = get_redis_client(request)

    username = payload.username
    password = payload.password

    # radcheck: PAP credential'ları (seed'e göre Cleartext-Password bcrypt hash içerir).
    radcheck_row = conn.execute(
        """
        SELECT value
        FROM radcheck
        WHERE username = %s
          AND attribute = 'Cleartext-Password'
          AND op = ':='
        LIMIT 1
        """,
        (username,),
    ).fetchone()

    if radcheck_row is None:
        # username bulunamadı
        return JSONResponse(
            status_code=401,
            content={"reply:Reply-Message": "Auth failed: user not found"},
        )

    # radusergroup: authorization/aktiflik kontrolü (bu adımda seed uyumlu olacak şekilde
    # "radusergroup yoksa passive/disabled" kabul ediyoruz).
    rg_row = conn.execute(
        """
        SELECT 1
        FROM radusergroup
        WHERE username = %s
        LIMIT 1
        """,
        (username,),
    ).fetchone()

    if rg_row is None:
        return JSONResponse(
            status_code=403,
            content={"reply:Reply-Message": "Auth failed: account is inactive"},
        )

    stored_hash: str = radcheck_row[0]

    # stored_hash: pgcrypto::crypt ile üretilen bcrypt formatı (ör. $2a$06$...)
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        # Hash formatı beklenenden farklıysa güvenli şekilde reject
        ok = False

    if not ok:
        return JSONResponse(
            status_code=401,
            content={"reply:Reply-Message": "Auth failed: wrong password"},
        )

    # Accepted: FreeRADIUS tarafından kabul edilmesi için HTTP 200 yeterli.
    # İsterseniz ileride ek FreeRADIUS control/reply attribute'ları ekleyebiliriz.
    return JSONResponse(
        status_code=200,
        content={
            "reply:Reply-Message": "Auth accepted",
            "control:Auth-Type": "PAP",
        },
    )

