from __future__ import annotations

from typing import Any

import fit.ai.nutrition.data_models as dm


def nutritional_info_from_row(result: dict[str, Any]) -> dm.NutritionalInformation:
    defaults = {
        "calories": 0,
        "protein": 0,
        "carbohydrates": 0,
        "fat": 0,
        "fiber": 0,
        "vitamin_a": 0,
        "vitamin_c": 0,
        "vitamin_d": 0,
        "calcium": 0,
        "iron": 0,
        "potassium": 0,
        "sodium": 0,
        "creatine": 0,
    }
    data = {**defaults, **{k: result[k] for k in defaults if k in result}}
    return dm.NutritionalInformation(
        calories=data["calories"],
        macronutrients=dm.Macronutrients(
            protein=data["protein"],
            carbohydrates=dm.Carbohydrates(
                total=data["carbohydrates"],
                fiber=data["fiber"],
                total_sugar=0,
                added_sugar=0,
            ),
            fat=dm.Fats(total=data["fat"], saturated=0, trans=0),
        ),
        micronutrients=dm.Micronutrients(
            vitamin_a=data["vitamin_a"],
            vitamin_c=data["vitamin_c"],
            vitamin_d=data["vitamin_d"],
            calcium=data["calcium"],
            iron=data["iron"],
            potassium=data["potassium"],
            sodium=data["sodium"],
        ),
        conditional_nutrients=dm.ConditionalNutrients(creatine=data.get("creatine", 0)),
    )
