from __future__ import annotations

import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from fit.backend.auth import create_token_pair, get_current_user_id, refresh_tokens
from fit.backend.app.api.models.auth import LoginRequest, RefreshRequest, TokenPair, User
from fit.backend.database.database import DatabaseService
from fit.backend.database.schema import (
    Inventory,
    Meal,
    Measurement,
    OAuthState,
    Profile,
    Supplement,
    SupplementEntry,
    TrackerAccount,
    User as DbUser,
    Water,
)
from fit.backend.app.deps import get_database_service

from fit.backend.app.api.main import api_router

app = FastAPI(title="Fit JSON API")
app.include_router(api_router)
# Initialize database service within FastAPI app state
tables = [
    ("users", DbUser, ["user_id"], "user_id"),
    ("meals", Meal, ["user_id"], "rowid"),
    ("supplements", Supplement, ["name", "user_id"], "rowid"),
    ("measurements", Measurement, ["user_id"], "rowid"),
    ("water", Water, ["user_id"], "rowid"),
    ("profile", Profile, ["user_id"], "user_id"),
    ("inventory", Inventory, ["user_id"], "rowid"),
    ("supplement_entries", SupplementEntry, ["user_id", "supplement_id"], "rowid"),
    ("tracker_accounts", TrackerAccount, ["user_id", "provider", "provider_user_id"], "rowid"),
    ("oauth_state", OAuthState, ["state"], "state"),
]
db_path = os.getenv("FIT_DB_PATH", "data/nutrition.db")
app.state.database_service = DatabaseService(db_path, tables)

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
def get_me(user_id: int = Depends(get_current_user_id), database_service: DatabaseService = Depends(get_database_service)):
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
