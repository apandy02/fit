from datetime import datetime
from typing import Optional

import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from PIL import Image

import fit.nutrition.assistants as assistants
import fit.nutrition.data_models as dm
from fit.backend.auth import get_current_user_id
from fit.backend.app.api.models.nutrition import (
    AnalysisRequest,
    AnalysisResult,
    MealItem,
    MealLog,
    SupplementCreate,
    SupplementLogRequest,
    WaterLogRequest,
    RegenerateAnalysisRequest,
)
from fit.web.common import database_service
from fit.web.common import micronutrient_goals
from fit.nutrition.targets import calculate_macro_targets
from fit.nutrition.data_models import WeightGoal
from fit.utils.calendar import get_current_week_dates

router = APIRouter(tags=["meals"], prefix="/meals")


@router.post("/nutrition/analyze", response_model=AnalysisResult)
def analyze(req: AnalysisRequest, user_id: int = Depends(get_current_user_id)):
    result = assistants.natural_language_nutritional_breakdown(req.text).content[0].parsed
    return AnalysisResult(
        title=result.title,
        ingredients=result.ingredients,
        calories=result.calories,
        protein=result.macronutrients.protein,
        carbohydrates=result.macronutrients.carbohydrates.total,
        fat=result.macronutrients.fat.total,
        fiber=result.macronutrients.carbohydrates.fiber,
        vitamin_a=result.micronutrients.vitamin_a,
        vitamin_c=result.micronutrients.vitamin_c,
        vitamin_d=result.micronutrients.vitamin_d,
        calcium=result.micronutrients.calcium,
        iron=result.micronutrients.iron,
        potassium=result.micronutrients.potassium,
        sodium=result.micronutrients.sodium,
        creatine=result.conditional_nutrients.creatine,
    )


@router.post("/nutrition/analyze-image", response_model=AnalysisResult)
async def analyze_image(
    additional_context: str = Form(""),
    meal_time: str = Form(...),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    result = assistants.vision_nutritional_breakdown(image, additional_context).content[0].parsed
    return AnalysisResult(
        title=result.title,
        ingredients=result.ingredients,
        calories=result.calories,
        protein=result.macronutrients.protein,
        carbohydrates=result.macronutrients.carbohydrates.total,
        fat=result.macronutrients.fat.total,
        fiber=result.macronutrients.carbohydrates.fiber,
        vitamin_a=result.micronutrients.vitamin_a,
        vitamin_c=result.micronutrients.vitamin_c,
        vitamin_d=result.micronutrients.vitamin_d,
        calcium=result.micronutrients.calcium,
        iron=result.micronutrients.iron,
        potassium=result.micronutrients.potassium,
        sodium=result.micronutrients.sodium,
        creatine=result.conditional_nutrients.creatine,
    )


@router.get("/meals", response_model=list[MealLog])
def get_meals(date_str: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    if date_str is None:
        day = datetime.today().date()
    else:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = datetime.today().date()
    meals = database_service.get_daily_meals(day, user_id)
    result: list[MealLog] = []
    for row in meals:
        meal = row["meal"]
        item = MealItem(
            title=meal.title,
            ingredients=meal.ingredients,
            calories=meal.calories,
            protein=meal.macronutrients.protein,
            carbohydrates=meal.macronutrients.carbohydrates.total,
            fat=meal.macronutrients.fat.total,
            fiber=meal.macronutrients.carbohydrates.fiber,
            vitamin_a=meal.micronutrients.vitamin_a,
            vitamin_c=meal.micronutrients.vitamin_c,
            vitamin_d=meal.micronutrients.vitamin_d,
            calcium=meal.micronutrients.calcium,
            iron=meal.micronutrients.iron,
            potassium=meal.micronutrients.potassium,
            sodium=meal.micronutrients.sodium,
            creatine=meal.conditional_nutrients.creatine,
            meal_time=row["meal_time"].strftime("%H:%M"),
            date_entered=day,
        )
        result.append(MealLog(id=row["rowid"], meal_time=item.meal_time, item=item))
    return result


@router.post("/meals", response_model=MealLog, status_code=201)
def create_meal(item: MealItem, user_id: int = Depends(get_current_user_id)):
    day = item.date_entered or datetime.today().date()
    meal_dm = _dm_from_meal_item(item)
    # Normalize time to HH:MM:SS for DB compatibility
    mt = item.meal_time
    try:
        t = datetime.strptime(mt, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(mt, "%H:%M:%S").time()
        except ValueError:
            # Fallback if an ISO datetime string gets passed
            t = datetime.fromisoformat(mt).time()
    mt_str = t.strftime("%H:%M:%S")
    database_service.insert_meal(
        meal_description=item.title,
        meal=meal_dm,
        meal_date=day,
        meal_time=mt_str,
        user_id=user_id,
        summary=item.title,
        ingredients=item.ingredients,
    )
    meals = database_service.get_daily_meals(day, user_id)
    created = next((m for m in meals if m["meal"].title == item.title and m["meal_time"].strftime("%H:%M") == item.meal_time), None)
    if created is None:
        raise HTTPException(status_code=500, detail="Meal not created")
    return MealLog(id=created["rowid"], meal_time=item.meal_time, item=item)


@router.delete("/meals/{meal_id}", status_code=204)
def delete_meal(meal_id: int, user_id: int = Depends(get_current_user_id)):
    ok = database_service.delete_meal(meal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meal not found")
    return None



@router.post("/supplements", status_code=201)
def save_supplement(body: SupplementCreate, user_id: int = Depends(get_current_user_id)):
    nutrition_info = dm.NutritionalInformation(
        calories=body.calories,
        macronutrients=dm.Macronutrients(
            protein=body.protein,
            carbohydrates=dm.Carbohydrates(
                total=body.carbohydrates,
                fiber=body.fiber,
                total_sugar=0,
                added_sugar=0,
            ),
            fat=dm.Fats(total=body.fat, saturated=0, trans=0),
        ),
        micronutrients=dm.Micronutrients(
            vitamin_a=body.vitamin_a,
            vitamin_c=body.vitamin_c,
            vitamin_d=body.vitamin_d,
            calcium=body.calcium,
            iron=body.iron,
            potassium=body.potassium,
            sodium=body.sodium,
        ),
        conditional_nutrients=dm.ConditionalNutrients(creatine=0),
    )
    day = body.date_entered or datetime.today().date()
    # Normalize time to HH:MM:SS
    try:
        t = datetime.strptime(body.time_consumed, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(body.time_consumed, "%H:%M:%S").time()
        except ValueError:
            t = datetime.fromisoformat(body.time_consumed).time()
    time_str = t.strftime("%H:%M:%S")
    database_service.insert_supplement(
        name=body.title,
        consumption_time=time_str,
        nutritional_info=nutrition_info,
        date=day,
        user_id=user_id,
    )
    return {"status": "created"}


@router.get("/supplements", response_model=list[str])
def get_supplements(user_id: int = Depends(get_current_user_id)):
    return database_service.get_supplement_names(user_id)


@router.post("/supplements/log", status_code=201)
def log_supplement_consumption(req: SupplementLogRequest, user_id: int = Depends(get_current_user_id)):
    info = database_service.get_supplement(req.supplement_name, user_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Unknown supplement")
    day = req.date_entered or datetime.today().date()
    try:
        t = datetime.strptime(req.time_consumed, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(req.time_consumed, "%H:%M:%S").time()
        except ValueError:
            t = datetime.fromisoformat(req.time_consumed).time()
    time_str = t.strftime("%H:%M:%S")
    database_service.insert_supplement(
        name=req.supplement_name,
        consumption_time=time_str,
        nutritional_info=info,
        date=day,
        user_id=user_id,
    )
    return {"status": "logged"}


@router.post("/water", status_code=201)
def log_water(req: WaterLogRequest, user_id: int = Depends(get_current_user_id)):
    day = req.date_entered or datetime.today().date()
    try:
        t = datetime.strptime(req.time_consumed, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(req.time_consumed, "%H:%M:%S").time()
        except ValueError:
            t = datetime.fromisoformat(req.time_consumed).time()
    time_str = t.strftime("%H:%M:%S")
    database_service.insert_water_consumption(
        water_consumed_ml=req.amount_ml,
        date_consumed=day,
        time_consumed=time_str,
        user_id=user_id,
    )
    return {"status": "logged"}


@router.post("/nutrition/regenerate", response_model=AnalysisResult)
def regenerate_analysis(req: RegenerateAnalysisRequest, user_id: int = Depends(get_current_user_id)):
    try:
        original = dm.MealBreakdown.model_validate(req.original_breakdown)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid original_breakdown payload")
    result = assistants.improve_breakdown(original, req.feedback).content[0].parsed
    return AnalysisResult(
        title=result.title,
        ingredients=result.ingredients,
        calories=result.calories,
        protein=result.macronutrients.protein,
        carbohydrates=result.macronutrients.carbohydrates.total,
        fat=result.macronutrients.fat.total,
        fiber=result.macronutrients.carbohydrates.fiber,
        vitamin_a=result.micronutrients.vitamin_a,
        vitamin_c=result.micronutrients.vitamin_c,
        vitamin_d=result.micronutrients.vitamin_d,
        calcium=result.micronutrients.calcium,
        iron=result.micronutrients.iron,
        potassium=result.micronutrients.potassium,
        sodium=result.micronutrients.sodium,
        creatine=result.conditional_nutrients.creatine,
    )


@router.post("/nutrition/overview/daily", response_model=dm.NutritionFeedback)
def generate_daily_overview(date_str: Optional[str] = None, user_id: int = Depends(get_current_user_id)):
    if date_str is None:
        day = datetime.today().date()
    else:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = datetime.today().date()
    meals = database_service.get_daily_meals(day, user_id)
    data = _get_user_nutritional_data_for_dates(user_id, [day])
    try:
        feedback = assistants.daily_io_analysis(meals, data["targets"][0], data["restrictions"]).content[0].parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return feedback


@router.post("/nutrition/overview/weekly", response_model=dm.NutritionFeedback)
def generate_weekly_overview(user_id: int = Depends(get_current_user_id)):
    days = get_current_week_dates()
    meals = {str(day): database_service.get_daily_meals(day, user_id) for day in days}
    data = _get_user_nutritional_data_for_dates(user_id, days)
    feedback = assistants.weekly_io_analysis(meals, data["targets"], data["restrictions"]).content[0].parsed
    return feedback


@router.post("/nutrition/suggestions/{nutrient}", response_model=dm.Recommendations)
def get_nutrient_suggestions(nutrient: str, user_id: int = Depends(get_current_user_id)):
    today = datetime.today().date()
    daily_nutrition = database_service.get_daily_cumulative_nutrition(today, user_id)
    data = _get_user_nutritional_data_for_dates(user_id, [today])
    user_preferences = assistants.summarize_user_preferences(database_service.get_all_meal_summaries(user_id))
    kitchen_inventory = database_service.get_inventory(user_id)
    recs = assistants.make_recommendations(
        consumption=daily_nutrition,
        targets=data["targets"][0],
        target_nutrient=nutrient,
        restrictions=data["restrictions"],
        user_preferences=user_preferences,
        kitchen_inventory=kitchen_inventory,
    ).content[0].parsed
    return recs


def _dm_from_meal_item(mi: MealItem) -> dm.NutritionalInformation | dm.MealBreakdown:
    macros = dm.Macronutrients(
        protein=mi.protein,
        carbohydrates=dm.Carbohydrates(total=mi.carbohydrates, fiber=mi.fiber, total_sugar=0, added_sugar=0),
        fat=dm.Fats(total=mi.fat, saturated=0, trans=0),
    )
    micros = dm.Micronutrients(
        vitamin_a=mi.vitamin_a,
        vitamin_c=mi.vitamin_c,
        vitamin_d=mi.vitamin_d,
        calcium=mi.calcium,
        iron=mi.iron,
        potassium=mi.potassium,
        sodium=mi.sodium,
    )
    cond = dm.ConditionalNutrients(creatine=mi.creatine)
    return dm.MealBreakdown(
        title=mi.title,
        ingredients=mi.ingredients,
        calories=mi.calories,
        macronutrients=macros,
        micronutrients=micros,
        conditional_nutrients=cond,
    )


def _get_user_nutritional_data_for_dates(user_id: int, days: list[datetime.date]):
    # NOTE: Tracker calories_burned not available server-side here; defaulting to 2000.
    weight_goal = WeightGoal(database_service.get_weight_goal(user_id))
    calories_burned = [2000 for _ in days]
    targets = [calculate_macro_targets(cb, weight_goal) for cb in calories_burned]
    for target in targets:
        target.update(micronutrient_goals)
    return {
        "targets": targets,
        "daily_nutrition": [database_service.get_daily_cumulative_nutrition(day, user_id) for day in days],
        "weight_goal": weight_goal,
        "restrictions": database_service.get_dietary_restrictions(user_id),
        "calories_burned": calories_burned,
    }
