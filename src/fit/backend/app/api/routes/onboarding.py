from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from fit.backend.app.api.models.onboarding import (
    ActivitySelectionRequest,
    DietaryCompletionRequest,
    GoalsSelectionRequest,
    MeasurementsCompletionRequest,
    OnboardingStatus,
    ProfileCompletionRequest,
)
from fit.backend.app.deps import get_database_service
from fit.backend.auth import get_current_user_id
from fit.backend.database.database import Database

router = APIRouter(tags=["onboarding"], prefix="/onboarding")


@router.get("/status", response_model=OnboardingStatus)
def get_status(
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    data = database_service.get_profile_data(user_id)
    return OnboardingStatus(onboarding_stage=int(data.get("onboarding_stage") or 0))


@router.post("/complete_profile")
def complete_profile(
    body: ProfileCompletionRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    form_data = body.model_dump(exclude_none=True)
    form_data["user_id"] = user_id
    form_data["onboarding_stage"] = 1
    ok = database_service.update_profile(form_data)
    if ok is False:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return {"status": "ok"}


@router.post("/complete_measurements")
def complete_measurements(
    body: MeasurementsCompletionRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    try:
        database_service.update_profile({"user_id": user_id, "onboarding_stage": 2})
        height_total_inches = body.height_feet * 12 + body.height_inches
        database_service.insert_measurement(
            user_id=user_id,
            weight=body.weight,
            height=height_total_inches,
            date=datetime.today().date(),
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete_dietary")
def complete_dietary(
    body: DietaryCompletionRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    restrictions_str = (
        ",".join(body.existing_restrictions) if body.existing_restrictions else ""
    )
    ok = database_service.update_profile(
        {
            "user_id": user_id,
            "dietary_restrictions": restrictions_str,
            "onboarding_stage": 3,
        }
    )
    if ok is False:
        raise HTTPException(
            status_code=500, detail="Failed to update dietary preferences"
        )
    return {"status": "ok"}


@router.post("/handle_activity_selection")
def handle_activity_selection(
    body: ActivitySelectionRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    ok = database_service.update_profile(
        {
            "user_id": user_id,
            "activity_level": body.activity_level,
            "onboarding_stage": 4,
        }
    )
    if ok is False:
        raise HTTPException(status_code=500, detail="Failed to update activity level")
    return {"status": "ok"}


@router.post("/handle_goals_selection")
def handle_goals_selection(
    body: GoalsSelectionRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    ok = database_service.update_profile(
        {
            "user_id": user_id,
            "weight_goal": body.weight_goal,
            "onboarding_stage": 5,
        }
    )
    if ok is False:
        raise HTTPException(status_code=500, detail="Failed to update goals")
    return {"status": "ok"}
