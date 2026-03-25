from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..database import get_postgres_conn, get_redis_client
from ..schemas import AuthorizeRequest

router = APIRouter(tags=["authorize"])


def _get_primary_group(conn, username: str) -> str | None:
    # priority küçük olan daha yüksek öncelik gibi davranır (FreeRADIUS örnek şemalarına uyumlu).
    row = conn.execute(
        """
        SELECT groupname
        FROM radusergroup
        WHERE username = %s
        ORDER BY priority ASC, groupname ASC
        LIMIT 1
        """,
        (username,),
    ).fetchone()
    return None if row is None else row[0]


def _get_group_replies(conn, groupname: str) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT attribute, value
        FROM radgroupreply
        WHERE groupname = %s
        """,
        (groupname,),
    ).fetchall()
    out: dict[str, str] = {}
    for attr, val in rows:
        # Aynı attribute birden fazla kez gelirse "son yazan kazanır" yaklaşımı (sade).
        out[str(attr)] = str(val)
    return out


@router.post("/authorize")
async def authorize(request: Request, payload: AuthorizeRequest):
    """
    Authorization:
    - kullanıcı -> grup (radusergroup)
    - grup -> VLAN/policy attribute'ları (radgroupreply)

    FreeRADIUS rlm_rest JSON formatına uygun olarak reply listesine attribute döndürür.
    """
    conn = get_postgres_conn(request)
    _ = get_redis_client(request)  # altyapı hazır kalsın; caching'i sonraki adımda yaparız.

    username = payload.username
    groupname = _get_primary_group(conn, username)
    if groupname is None:
        return JSONResponse(
            status_code=403,
            content={"reply:Reply-Message": "Authorization failed: user has no group"},
        )

    replies = _get_group_replies(conn, groupname)

    # VLAN için beklediğimiz attribute'lar:
    # - Tunnel-Medium-Type (IEEE-802)
    # - Tunnel-Private-Group-Id (VLAN ID)
    vlan_id = replies.get("Tunnel-Private-Group-Id")
    if not vlan_id:
        return JSONResponse(
            status_code=403,
            content={"reply:Reply-Message": f"Authorization failed: group '{groupname}' has no VLAN mapping"},
        )

    # FreeRADIUS sözlüğünde Tunnel-Type genelde enum string "VLAN" olarak parse edilebilir.
    # Tunnel-Medium-Type seed'de var; yoksa güvenli default kullanıyoruz.
    tunnel_medium = replies.get("Tunnel-Medium-Type", "IEEE-802")

    return JSONResponse(
        status_code=200,
        content={
            "reply:Reply-Message": f"Authorized: group={groupname} vlan={vlan_id}",
            "reply:Tunnel-Type": "VLAN",
            "reply:Tunnel-Medium-Type": tunnel_medium,
            "reply:Tunnel-Private-Group-Id": vlan_id,
        },
    )

