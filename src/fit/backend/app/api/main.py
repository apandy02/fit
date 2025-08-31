from fastapi import APIRouter

from fit.backend.app.api.routes import nutrition, kitchen, performance, rest

api_router = APIRouter()
api_router.include_router(nutrition.router)
api_router.include_router(kitchen.router)
api_router.include_router(performance.router)
api_router.include_router(rest.router)

