from fastapi import APIRouter

from fit.backend.app.api.routes import (
    nutrition,
    kitchen,
    performance,
    rest,
    tracker_oauth,
    user_profile,
    onboarding,
)

api_router = APIRouter()
api_router.include_router(nutrition.router)
api_router.include_router(kitchen.router)
api_router.include_router(performance.router)
api_router.include_router(rest.router)
api_router.include_router(tracker_oauth.router)
api_router.include_router(user_profile.router)
api_router.include_router(onboarding.router)
