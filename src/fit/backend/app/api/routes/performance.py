import datetime

from fastapi import APIRouter, Depends, HTTPException

import fit.ai.performance.assistants as assistants
from fit.backend.auth import get_current_user_id
from fit.backend.services.tracker_service import get_primary_tracker_for_user
from fit.backend.database.database import Database
from fit.backend.app.deps import get_database_service
from fit.backend.app.api.models.performance import (
    PerformanceDailyInfoResponse,
    PerformanceOverviewResponse,
)
from fit.ai.nutrition.targets import WeightGoal, calculate_caloric_target
from fit.utils.conversions import convert_nutrient_unit, NutrientUnit




router = APIRouter(tags=["performance"], prefix="/performance")


@router.get("/daily-info", response_model=PerformanceDailyInfoResponse)
def get_daily_info(user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    t = get_primary_tracker_for_user(database_service, user_id)
    today = datetime.date.today()
    if t.tracker_type == "whoop":
        cycle = t.get_cycle_for_day(today)
        daily_stats = cycle["score"]
        daily_stats["calories"] = convert_nutrient_unit(daily_stats["kilojoule"], NutrientUnit.kJ, NutrientUnit.kcal)
    else:
        _ = t.get_intraday_heart_rate(today)
        daily_stats = {
            "calories": t.get_daily_calories_burned(today),
            "average_heart_rate": 55,
            "max_heart_rate": 100,
        }
    workouts = t.get_daily_workouts(today)
    return PerformanceDailyInfoResponse(daily_stats=daily_stats, workouts=workouts)


@router.post("/overview", response_model=PerformanceOverviewResponse)
def generate_overview(user_id: int = Depends(get_current_user_id), database_service: Database = Depends(get_database_service)):
    try:
        t = get_primary_tracker_for_user(database_service, user_id)
        today = datetime.date.today()
        # daily info
        if t.tracker_type == "whoop":
            cycle = t.get_cycle_for_day(today)
            daily_stats = cycle["score"]
            daily_stats["calories"] = convert_nutrient_unit(daily_stats["kilojoule"], NutrientUnit.kJ, NutrientUnit.kcal)
        else:
            _ = t.get_intraday_heart_rate(today)
            daily_stats = {
                "calories": t.get_daily_calories_burned(today),
                "average_heart_rate": 55,
                "max_heart_rate": 100,
            }
        workouts = t.get_daily_workouts(today)
        daily_nutrition = database_service.meals.get_daily_cumulative_nutrition(today, user_id)
        caloric_consumption = daily_nutrition.calories
        caloric_target = calculate_caloric_target(daily_nutrition, WeightGoal.MAINTAIN)
        workout_trend_summary = assistants.summarize_workout_trends(workouts)
        current_time = datetime.datetime.now().time()
        time_cutoff = datetime.time(hour=20)

        analysis = assistants.early_daily_performance_overview(
            daily_stats=daily_stats,
            activities=workouts,
            caloric_target=caloric_target,
            caloric_consumption=caloric_consumption,
            workout_trend_summary=workout_trend_summary,
            time=current_time,
            time_cutoff=time_cutoff,
        )
        # assistants returns a list[ell.Message] in code but upstream uses .content[0].parsed in similar spots
        # converting to string for JSON response
        return PerformanceOverviewResponse(analysis=str(analysis))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


