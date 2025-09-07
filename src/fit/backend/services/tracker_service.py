import datetime

from fastapi import HTTPException

from fit.backend.trackers.manager import tracker_factory
from fit.backend.database.postgres_service import PostgresDatabaseService


def _is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    try:
        return datetime.datetime.fromisoformat(expires_at) <= datetime.datetime.utcnow()
    except Exception:
        return False


def get_primary_tracker_for_user(database_service: PostgresDatabaseService, user_id: int):
    acct = database_service.get_tracker_account(user_id, provider=None, primary_only=True)
    if not acct:
        raise HTTPException(status_code=409, detail="No tracker linked")
    # TODO: implement refresh if _is_expired(acct["expires_at"]) and refresh_token present
    return tracker_factory(acct["provider"], acct["access_token"])


