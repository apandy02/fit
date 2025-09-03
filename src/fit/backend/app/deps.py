from __future__ import annotations

from fastapi import Request

from fit.backend.database.database import DatabaseService


def get_database_service(request: Request) -> DatabaseService:
    """Return the DatabaseService attached to the FastAPI app state."""
    return request.app.state.database_service


