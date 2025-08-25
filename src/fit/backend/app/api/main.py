from fastapi import APIRouter

from fit.backend.app.api.routes import meals

api_router = APIRouter()
api_router.include_router(meals.router)

