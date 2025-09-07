from __future__ import annotations

from fastapi import Request

from fit.backend.database.postgres_service import PostgresDatabaseService


def get_database_service(request: Request) -> PostgresDatabaseService:
    """Return the DatabaseService attached to the FastAPI app state."""
    return request.app.state.database_service


