from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

import fit.nutrition.assistants as assistants
import fit.nutrition.data_models as dm
from fit.backend.auth import get_current_user_id
from fit.backend.app.api.models.meals import (AnalysisRequest, AnalysisResult,
                                              MealItem, MealLog)
from fit.web.common import database_service

router = APIRouter(tags=["meals"], prefix="/meals")

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


