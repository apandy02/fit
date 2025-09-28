import io
from datetime import datetime
from typing import Optional

import openfoodfacts
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image

import fit.ai.nutrition.assistants as assistants
import fit.ai.nutrition.data_models as dm
from fit.ai.nutrition.data_models import WeightGoal
from fit.ai.nutrition.targets import MICRO_GOALS, calculate_macro_targets
from fit.backend.app.api.models.nutrition import (AnalysisRequest,
                                                  AnalysisResult, MealItem,
                                                  MealLog,
                                                  RegenerateAnalysisRequest,
                                                  SupplementCreate,
                                                  SupplementLogRequest,
                                                  WaterLogRequest)
from fit.backend.app.deps import get_database_service
from fit.backend.auth import get_current_user_id
from fit.backend.database.database import Database
from fit.utils.calendar import get_current_week_dates

router = APIRouter(tags=["nutrition"], prefix="/nutrition")


@router.post("/analyze-meal", response_model=AnalysisResult)
async def analyze(req: AnalysisRequest, user_id: int = Depends(get_current_user_id)):
    result = await assistants.natural_language_nutritional_breakdown(req.text)
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


@router.post("/analyze-meal-image", response_model=AnalysisResult)
async def analyze_image(
    additional_context: str = Form(""),
    meal_time: str = Form(...),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    result = await assistants.vision_nutritional_breakdown(image, additional_context)
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


@router.get("/barcode/{code}", response_model=AnalysisResult)
def lookup_by_barcode(code: str, user_id: int = Depends(get_current_user_id)):
    api = openfoodfacts.API(user_agent="fit/1.0")
    try:
        product = api.product.get(code=code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenFoodFacts error: {str(e)}")
    if (
        not product
        or "nutriments" not in product
        or not product.get("nutrition_data", False)
    ):
        raise HTTPException(
            status_code=404, detail="Product not found or nutrition data unavailable"
        )

    nutriments: dict = product.get("nutriments", {})
    nutrition_data_per = product["nutrition_data_per"]

    # Macros and calories
    calories = nutriments[f"energy-kcal_{nutrition_data_per}"] or 0.0
    protein = nutriments.get("proteins", 0.0)
    carbohydrates = nutriments.get(
        f"carbohydrates_{nutrition_data_per}", 0.0
    ) or nutriments.get("carbohydrates", 0.0)
    fat = nutriments.get(f"fat_{nutrition_data_per}", 0.0) or nutriments.get("fat", 0.0)
    fiber = nutriments.get(f"fiber_{nutrition_data_per}", 0.0) or nutriments.get(
        "fiber", 0.0
    )

    # Assume all micronutrients are already in mg
    vitamin_a = nutriments.get(f"vitamin-a_{nutrition_data_per}", 0.0)
    vitamin_c = nutriments.get(f"vitamin-c_{nutrition_data_per}", 0.0)
    vitamin_d = nutriments.get(f"vitamin-d_{nutrition_data_per}", 0.0)
    calcium = nutriments.get(f"calcium_{nutrition_data_per}", 0.0)
    iron = nutriments.get(f"iron_{nutrition_data_per}", 0.0)
    potassium = nutriments.get(f"potassium_{nutrition_data_per}", 0.0)
    sodium = nutriments.get(
        f"sodium_{nutrition_data_per}", 0.0
    )  # TODO: Rearchitect with more modular approach

    title = product.get("product_name") or product.get("brands") or "Unknown product"
    ingredients = (
        product.get("ingredients_text_en")
        or product.get("ingredients_text")
        or product.get("generic_name_en")
        or ""
    )

    return AnalysisResult(
        title=title,
        ingredients=ingredients,
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fat=fat,
        fiber=fiber,
        vitamin_a=vitamin_a,
        vitamin_c=vitamin_c,
        vitamin_d=vitamin_d,
        calcium=calcium,
        iron=iron,
        potassium=potassium,
        sodium=sodium,
        creatine=0.0,
    )


@router.get("/meals", response_model=list[MealLog])
def get_meals(
    date_str: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    if date_str is None:
        day = datetime.today().date()
    else:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = datetime.today().date()
    meals = database_service.meals.get_daily_meals(day, user_id)
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
def create_meal(
    item: MealItem,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    day = item.date_entered or datetime.today().date()
    meal_dm = _dm_from_meal_item(item)
    # Normalize time to HH:MM:SS for DB compatibility
    mt = item.meal_time
    try:
        t = datetime.strptime(mt, "%H:%M:%S").time()
    except ValueError:
        try:
            t = datetime.strptime(mt, "%H:%M").time()
        except ValueError:
            # Fallback if an ISO datetime string gets passed
            t = datetime.fromisoformat(mt).time()
    mt_str = t.strftime("%H:%M:%S")
    database_service.meals.insert_meal(
        meal_description=item.title,
        meal=meal_dm,
        meal_date=day,
        meal_time=mt_str,
        user_id=user_id,
        summary=item.title,
        ingredients=item.ingredients,
    )
    meals = database_service.meals.get_daily_meals(day, user_id)
    created = next(
        (
            m
            for m in meals
            if m["meal"].title == item.title
            and m["meal_time"].strftime("%H:%M:%S") == mt_str
        ),
        None,
    )
    if created is None:
        raise HTTPException(status_code=500, detail="Meal not created")
    return MealLog(id=created["rowid"], meal_time=mt_str, item=item)



@router.delete("/meals/{meal_id}", status_code=204)
def delete_meal(
    meal_id: int,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    ok = database_service.meals.delete_meal(meal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meal not found")
    return None


@router.post("/supplements", status_code=201)
def save_supplement(
    body: SupplementCreate,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
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
    database_service.supplements.insert_supplement(
        name=body.title,
        nutritional_info=nutrition_info,
        user_id=user_id,
    )
    # also log a meal entry for now
    database_service.meals.insert_meal(
        body.title, nutrition_info, day, time_str, user_id, is_supplement=True
    )
    return {"status": "created"}


@router.get("/supplements", response_model=list[str])
def get_supplements(
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    return database_service.supplements.get_supplement_names(user_id)


@router.post("/supplements/log", status_code=201)
def log_supplement_consumption(
    req: SupplementLogRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    # Validate supplement exists
    info = database_service.supplements.get_supplement(req.supplement_name, user_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Unknown supplement")
    # Normalize time
    try:
        t = datetime.strptime(req.time_consumed, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(req.time_consumed, "%H:%M:%S").time()
        except ValueError:
            t = datetime.fromisoformat(req.time_consumed).time()
    time_str = t.strftime("%H:%M:%S")
    # Log consumption in entries table to avoid duplicate supplement row
    servings = getattr(req, "servings", 1.0)
    database_service.supplements.log_supplement_consumption(
        user_id=user_id,
        supplement_name=req.supplement_name,
        servings=servings,
        time_consumed=time_str,
    )
    return {"status": "logged"}


@router.post("/water", status_code=201)
def log_water(
    req: WaterLogRequest,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    day = req.date_entered or datetime.today().date()
    try:
        t = datetime.strptime(req.time_consumed, "%H:%M").time()
    except ValueError:
        try:
            t = datetime.strptime(req.time_consumed, "%H:%M:%S").time()
        except ValueError:
            t = datetime.fromisoformat(req.time_consumed).time()
    time_str = t.strftime("%H:%M:%S")
    database_service.water.insert_water_consumption(
        water_consumed_ml=req.amount_ml,
        date_consumed=day,
        time_consumed=time_str,
        user_id=user_id,
    )
    return {"status": "logged"}


@router.post("/regenerate-analysis", response_model=AnalysisResult)
async def regenerate_analysis(
    req: RegenerateAnalysisRequest, user_id: int = Depends(get_current_user_id)
):
    try:
        original = dm.MealBreakdown.model_validate(req.original_breakdown)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid original_breakdown payload"
        )
    result = await assistants.improve_breakdown(original, req.feedback)
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


@router.post("/overview/daily", response_model=dm.NutritionFeedback)
async def generate_daily_overview(
    date_str: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    if date_str is None:
        day = datetime.today().date()
    else:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = datetime.today().date()
    meals = database_service.meals.get_daily_meals(day, user_id)
    data = _get_user_nutritional_data_for_dates(user_id, [day], database_service)
    try:
        feedback = await assistants.daily_io_analysis(
            meals, data["targets"][0], data["restrictions"]
        )
    except Exception as e:
        print(f"Error in daily_io_analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return feedback


@router.post("/overview/weekly", response_model=dm.NutritionFeedback)
async def generate_weekly_overview(
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    days = get_current_week_dates()
    meals = {
        str(day): database_service.meals.get_daily_meals(day, user_id) for day in days
    }
    data = _get_user_nutritional_data_for_dates(user_id, days, database_service)
    feedback = await assistants.weekly_io_analysis(
        meals, data["targets"], data["restrictions"]
    )
    return feedback


@router.post("/suggestions/{nutrient}", response_model=dm.Recommendations)
async def get_nutrient_suggestions(
    nutrient: str,
    user_id: int = Depends(get_current_user_id),
    database_service: Database = Depends(get_database_service),
):
    today = datetime.today().date()
    daily_nutrition = database_service.meals.get_daily_cumulative_nutrition(
        today, user_id
    )
    data = _get_user_nutritional_data_for_dates(user_id, [today], database_service)
    user_preferences = await assistants.summarize_user_preferences(
        database_service.meals.get_all_meal_summaries(user_id)
    )
    kitchen_inventory = database_service.inventory.get_inventory(user_id)
    recs = await assistants.make_recommendations(
        consumption=daily_nutrition,
        targets=data["targets"][0],
        target_nutrient=nutrient,
        restrictions=data["restrictions"],
        user_preferences=user_preferences,
        kitchen_inventory=kitchen_inventory,
    )
    return recs


def _dm_from_meal_item(mi: MealItem) -> dm.NutritionalInformation | dm.MealBreakdown:
    macros = dm.Macronutrients(
        protein=mi.protein,
        carbohydrates=dm.Carbohydrates(
            total=mi.carbohydrates, fiber=mi.fiber, total_sugar=0, added_sugar=0
        ),
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


def _get_user_nutritional_data_for_dates(
    user_id: int, days: list[datetime.date], database_service: Database
):
    # NOTE: Tracker calories_burned not available server-side here; defaulting to 2000.
    weight_goal = WeightGoal(database_service.profile.get_weight_goal(user_id))
    calories_burned = [2000 for _ in days]
    targets = [calculate_macro_targets(cb, weight_goal) for cb in calories_burned]
    micronutrient_goals = MICRO_GOALS["male"]  # TODO: get gender from user
    for target in targets:
        target.update(micronutrient_goals)
    return {
        "targets": targets,
        "daily_nutrition": [
            database_service.meals.get_daily_cumulative_nutrition(day, user_id)
            for day in days
        ],
        "weight_goal": weight_goal,
        "restrictions": database_service.profile.get_dietary_restrictions(user_id),
        "calories_burned": calories_burned,
    }
