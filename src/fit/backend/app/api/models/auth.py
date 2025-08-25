from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class LoginRequest(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class User(BaseModel):
    user_id: int
    email: Optional[str] = None
    name: Optional[str] = None
