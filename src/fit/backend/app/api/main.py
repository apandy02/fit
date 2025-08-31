from fastapi import APIRouter

from fit.backend.app.api.routes import nutrition

api_router = APIRouter()
api_router.include_router(nutrition.router)

