import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from fit.backend.app.deps import get_database_service
from fit.backend.auth import get_current_user_id
from fit.backend.database.database import Database
from fit.backend.trackers.app_client_factory import (
    extract_provider_user_id,
    make_app_client,
)

router = APIRouter(tags=["oauth"], prefix="/oauth")


def _redirect_base() -> str:
    return os.environ.get("OAUTH_REDIRECT_BASE", "http://localhost:5002")


@router.post("/{provider}/start")
def oauth_start(
    provider: str,
    redirect_to: str | None = None,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    try:
        client = make_app_client(provider)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    state = secrets.token_urlsafe(24)
    now = datetime.now(datetime.timezone.utc)
    exp = now + timedelta(minutes=10)
    redirect_uri = f"{_redirect_base()}/oauth/{provider}/callback"

    database_service.accounts.create_oauth_state(
        state=state,
        code_verifier=client.code_verifier,
        provider=provider,
        user_id=user_id,
        redirect_to=redirect_to,
        created_at=now.isoformat(),
        expires_at=exp.isoformat(),
    )

    url = client.login_link(redirect_uri=redirect_uri, state=state)
    return RedirectResponse(url, status_code=303)


@router.get("/{provider}/callback")
def oauth_callback(
    provider: str,
    code: str,
    state: str,
    database_service: Database = Depends(get_database_service),
):
    st = database_service.accounts.consume_oauth_state(state)
    if not st or st.get("provider") != provider:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    try:
        client = make_app_client(provider, restore_code_verifier=st["code_verifier"])
        redirect_uri = f"{_redirect_base()}/oauth/{provider}/callback"
        tokens = client.fetch_access_token(code, redirect_uri)
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        expires_at = None
        if "expires_in" in tokens:
            expires_at = (
                datetime.utcnow() + timedelta(seconds=int(tokens["expires_in"]))
            ).isoformat()
        profile = client.get_info(access_token)
        provider_user_id = extract_provider_user_id(provider, profile)
        user_id = st.get("user_id")
        if user_id is None:
            # Create/find user by provider id
            # For now, ensure a user row exists; existing DB has users table with provider + provider_user_id
            uid = database_service.accounts.get_user_id(provider_user_id, provider)
            if uid is None:
                uid = database_service.accounts.insert_new_user(
                    {
                        "user_id": None,  # autogen if schema supports
                        "email": profile.get("email"),
                        "provider": provider,
                        "provider_user_id": provider_user_id,
                    }
                )
            user_id = uid

        database_service.accounts.upsert_tracker_account(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=None,
            primary=True,
        )
        target = st.get("redirect_to") or os.environ.get(
            "FRONTEND_OAUTH_SUCCESS", "/profile"
        )
        return RedirectResponse(target, status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{provider}")
def oauth_unlink(
    provider: str,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    acct = database_service.accounts.get_tracker_account(
        user_id, provider=provider, primary_only=False
    )
    if not acct:
        raise HTTPException(status_code=404, detail="Not linked")
    # Simple unlink by clearing tokens
    database_service.accounts.update_tracker_tokens(
        user_id, provider, access_token="", refresh_token=None, expires_at=None
    )
    return {"status": "unlinked"}


@router.get("/me/trackers")
def list_linked_trackers(
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    return database_service.accounts.list_tracker_accounts(user_id)


@router.patch("/me/trackers/primary")
def set_primary(
    provider: str,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    database_service.accounts.set_primary_tracker(user_id, provider)
    return {"status": "ok"}
