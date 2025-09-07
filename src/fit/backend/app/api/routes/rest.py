import datetime

from fastapi import APIRouter, Depends, HTTPException

import fit.ai.rest.assistants as assistants
from fit.backend.auth import get_current_user_id
from fit.backend.services.tracker_service import get_primary_tracker_for_user
from fit.backend.app.api.models.rest import RestDailyInfoResponse, RestOverviewResponse
from fit.backend.trackers.implementations.whoop import Whoop
from fit.backend.database.postgres_service import PostgresDatabaseService
from fit.backend.app.deps import get_database_service


router = APIRouter(tags=["rest"], prefix="/rest")


@router.get("/daily-info", response_model=RestDailyInfoResponse)
def get_daily_info(user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    t = get_primary_tracker_for_user(database_service, user_id)
    today = datetime.date.today()
    if t.tracker_type == "whoop":
        recovery = t.get_daily_recovery(today)
        if recovery is not None and len(recovery) > 0:
            scores = recovery["score"]
            recovery_data = {
                "recovery_score": scores["recovery_score"],
                "resting_heart_rate": scores["resting_heart_rate"],
                "hrv": scores["hrv_rmssd_milli"],
            }
        else:
            recovery_data = None
    else:
        recovery_data = {
            "resting_heart_rate": t.get_daily_resting_heart_rate(today),
            "hrv": t.get_daily_hrv(today),
            "recovery_score": None,
        }
    sleep = t.get_daily_sleep(today)
    return RestDailyInfoResponse(recovery=recovery_data, sleep=sleep)


@router.post("/overview", response_model=RestOverviewResponse)
def generate_overview(user_id: int = Depends(get_current_user_id), database_service: PostgresDatabaseService = Depends(get_database_service)):
    try:
        t = get_primary_tracker_for_user(database_service, user_id)
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        sleep_data = t.get_daily_sleep(yesterday)
        meals = database_service.get_daily_meals(yesterday, user_id)
        formatted_meals = [(datetime.datetime.combine(yesterday, m["meal_time"]), m["meal"]) for m in meals]
        activities = t.get_daily_workouts(yesterday)
        formatted_activities = [(a.start_time, a.type, a.intensity) for a in activities]
        if isinstance(t, Whoop):
            recovery = t.get_daily_recovery(yesterday)
            if recovery is not None and len(recovery) > 0:
                scores = recovery["score"]
                recovery_metrics = {
                    "recovery_score": scores["recovery_score"],
                    "resting_heart_rate": scores["resting_heart_rate"],
                    "hrv": scores["hrv_rmssd_milli"],
                }
            else:
                recovery_metrics = {"recovery_score": None, "resting_heart_rate": None, "hrv": None}
        else:
            recovery_metrics = {
                "resting_heart_rate": t.get_daily_resting_heart_rate(yesterday),
                "hrv": t.get_daily_hrv(yesterday),
                "recovery_score": None,
            }

        analysis = assistants.analyze_rest_patterns(
            sleep_data=sleep_data,
            meals=formatted_meals,
            activities=formatted_activities,
            sleep_targets=480.0,
            recovery_metrics=recovery_metrics,
        )
        return RestOverviewResponse(analysis=str(analysis))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


