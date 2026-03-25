from fastapi import APIRouter

from .auth import router as auth_router
from .authorize import router as authorize_router
from .accounting import router as accounting_router
from .users import router as users_router
from .sessions import router as sessions_router


def build_routes() -> APIRouter:
    r = APIRouter()
    r.include_router(auth_router)
    r.include_router(authorize_router)
    r.include_router(accounting_router)
    r.include_router(users_router)
    r.include_router(sessions_router)
    return r

