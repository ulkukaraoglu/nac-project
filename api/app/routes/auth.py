import bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..database import get_redis_client, get_postgres_conn
from ..schemas import AuthRequest

router = APIRouter(tags=["auth"])


def _rate_keys(username: str, source: str) -> tuple[str, str]:
    """
    Redis key isimlendirmesi: trace/izlenebilir olsun diye net prefix kullanıyoruz.
    - fail_key: pencere içinde başarısız deneme sayısı (TTL ile)
    - block_key: geçici blok (TTL ile)
    """
    base = f"nac:auth:rate:u:{username}:src:{source}"
    return f"{base}:fail", f"{base}:block"


async def _rate_is_blocked(redis, block_key: str) -> bool:
    return (await redis.exists(block_key)) == 1


async def _rate_record_failure(
    redis,
    fail_key: str,
    block_key: str,
    *,
    max_attempts: int,
    window_seconds: int,
    block_seconds: int,
) -> bool:
    """
    Bir başarısız denemeyi kaydeder.
    - fail_key: INCR + TTL(window_seconds)
    - count >= max_attempts => block_key set + (fail_key temizlenebilir)

    Dönen değer:
    - True: rate-limit tetiklendi ve block aktif oldu
    """
    count = await redis.incr(fail_key)
    ttl = await redis.ttl(fail_key)
    if ttl is None or ttl < 0:
        await redis.expire(fail_key, window_seconds)

    if int(count) >= int(max_attempts):
        await redis.set(block_key, "1", ex=block_seconds)
        await redis.delete(fail_key)
        return True

    return False


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
    cfg = request.app.state.settings
    conn = get_postgres_conn(request)
    redis = get_redis_client(request)

    username = payload.username
    password = payload.password
    source = payload.nas_ip_address or (request.client.host if request.client else "unknown")
    fail_key, block_key = _rate_keys(username, source)

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
        # Rate limiting: user not found da "başarısız deneme" sayılır.
        if await _rate_is_blocked(redis, block_key):
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: rate limited"},
            )

        rate_triggered = await _rate_record_failure(
            redis,
            fail_key,
            block_key,
            max_attempts=cfg.auth_rate_max_attempts,
            window_seconds=cfg.auth_rate_window_seconds,
            block_seconds=cfg.auth_rate_block_seconds,
        )

        if rate_triggered:
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: too many attempts; temporarily blocked"},
            )

        return JSONResponse(status_code=401, content={"reply:Reply-Message": "Auth failed: user not found"})

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
        # Rate limiting: pasif kullanıcı da başarısız deneme sayılır.
        if await _rate_is_blocked(redis, block_key):
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: rate limited"},
            )

        rate_triggered = await _rate_record_failure(
            redis,
            fail_key,
            block_key,
            max_attempts=cfg.auth_rate_max_attempts,
            window_seconds=cfg.auth_rate_window_seconds,
            block_seconds=cfg.auth_rate_block_seconds,
        )

        if rate_triggered:
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: too many attempts; temporarily blocked"},
            )

        return JSONResponse(status_code=403, content={"reply:Reply-Message": "Auth failed: account is inactive"})

    stored_hash: str = radcheck_row[0]

    # stored_hash: pgcrypto::crypt ile üretilen bcrypt formatı (ör. $2a$06$...)
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        # Hash formatı beklenenden farklıysa güvenli şekilde reject
        ok = False

    if not ok:
        # Rate limiting: yanlış parola da başarısız deneme sayılır.
        if await _rate_is_blocked(redis, block_key):
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: rate limited"},
            )

        rate_triggered = await _rate_record_failure(
            redis,
            fail_key,
            block_key,
            max_attempts=cfg.auth_rate_max_attempts,
            window_seconds=cfg.auth_rate_window_seconds,
            block_seconds=cfg.auth_rate_block_seconds,
        )

        if rate_triggered:
            return JSONResponse(
                status_code=403,
                content={"reply:Reply-Message": "Auth failed: too many attempts; temporarily blocked"},
            )

        return JSONResponse(status_code=401, content={"reply:Reply-Message": "Auth failed: wrong password"})

    # Accepted: FreeRADIUS tarafından kabul edilmesi için HTTP 200 yeterli.
    # İsterseniz ileride ek FreeRADIUS control/reply attribute'ları ekleyebiliriz.
    # Başarılı girişte sayaçları/blokları temizle.
    await redis.delete(fail_key)
    await redis.delete(block_key)

    return JSONResponse(
        status_code=200,
        content={
            "reply:Reply-Message": "Auth accepted",
            "control:Auth-Type": "PAP",
        },
    )

