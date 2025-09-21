from __future__ import annotations

import time
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Simple HMAC-less token format for local use: "uid:exp:rand"
# This keeps the repo free of external JWT dependency while providing expiring tokens.

SECURITY_SCHEME = HTTPBearer(auto_error=False)

ACCESS_TOKEN_TTL_SECONDS = 60 * 30  # 30 minutes
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _now() -> int:
    return int(time.time())


def _make_token(user_id: int, ttl_seconds: int, entropy: str) -> str:
    exp = _now() + ttl_seconds
    return f"{user_id}:{exp}:{entropy}"


def _parse_token(token: str) -> Tuple[int, int]:
    try:
        user_id_str, exp_str, _ = token.split(":", 2)
        return int(user_id_str), int(exp_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def create_token_pair(user_id: int) -> tuple[str, str, int]:
    access = _make_token(user_id, ACCESS_TOKEN_TTL_SECONDS, "a")
    refresh = _make_token(user_id, REFRESH_TOKEN_TTL_SECONDS, "r")
    return access, refresh, ACCESS_TOKEN_TTL_SECONDS


def refresh_tokens(refresh_token: str) -> tuple[str, str, int]:
    user_id, exp = _parse_token(refresh_token)
    if _now() >= exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh expired"
        )
    return create_token_pair(user_id)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(SECURITY_SCHEME),
) -> int:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    token = credentials.credentials
    user_id, exp = _parse_token(token)
    if _now() >= exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    return user_id
