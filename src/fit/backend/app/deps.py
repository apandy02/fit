from __future__ import annotations

from fastapi import Request

from fit.backend.database.database import Database


def get_database_service(request: Request) -> Database:
    """Return the DatabaseService attached to the FastAPI app state."""
    return request.app.state.database_service
