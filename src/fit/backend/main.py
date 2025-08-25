from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from fit.backend.auth import create_token_pair, get_current_user_id, refresh_tokens
from fit.backend.app.api.models.auth import LoginRequest, RefreshRequest, TokenPair, User
from fit.web.common import database_service

from fit.backend.app.api.main import api_router

app = FastAPI(title="Fit JSON API")
app.include_router(api_router)

# CORS
origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "exp://127.0.0.1:19000",
    "exp+fit://127.0.0.1:19000",
    "exp://localhost:19000",
    "exp+fit://localhost:19000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/me", response_model=User)
def get_me(user_id: int = Depends(get_current_user_id)):
    profile = database_service.get_profile_data(user_id)
    return User(user_id=user_id, email=profile.get("email"), name=profile.get("name"))


@app.post("/auth/login", response_model=TokenPair)
def login(req: LoginRequest):
    # For now, allow explicit user_id for local dev; in real use, integrate existing OAuth flow.
    if req.user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required for login")
    access, refresh, expires_in = create_token_pair(req.user_id)
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=expires_in)


@app.post("/auth/refresh", response_model=TokenPair)
def refresh(req: RefreshRequest):
    access, refresh_tok, expires_in = refresh_tokens(req.refresh_token)
    return TokenPair(access_token=access, refresh_token=refresh_tok, expires_in=expires_in)
