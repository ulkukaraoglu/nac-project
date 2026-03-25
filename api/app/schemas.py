from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    nas_ip_address: Optional[str] = None


class AuthResponse(BaseModel):
    result: Literal["accepted", "rejected", "not_implemented"] = "not_implemented"
    reason: Optional[str] = None


class AuthorizeRequest(BaseModel):
    username: str = Field(..., min_length=1)
    nas_ip_address: Optional[str] = None


class AuthorizeResponse(BaseModel):
    result: Literal["ok", "not_implemented"] = "not_implemented"
    vlan_id: Optional[int] = None
    policy_name: Optional[str] = None


class AccountingRequest(BaseModel):
    acct_session_id: str = Field(..., min_length=1)
    username: Optional[str] = None
    nas_ip_address: str

    session_time_seconds: Optional[int] = None
    input_octets: Optional[int] = None
    output_octets: Optional[int] = None

    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None


class AccountingResponse(BaseModel):
    result: Literal["recorded", "not_implemented"] = "not_implemented"
    reason: Optional[str] = None


class UserOut(BaseModel):
    username: str
    groups: list[str] = []


class SessionOut(BaseModel):
    username: str
    nas_ip_address: str
    start_time: datetime
    session_time_seconds: Optional[int] = None

