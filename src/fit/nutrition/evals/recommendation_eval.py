import ell
import os
import json
from fit.nutrition.assistants import make_recommendations, natural_language_macros
from fit.nutrition.data import NutritionalInformation, MealRecommendation, Recommendations
ell.init(store="./logdir")  # Enable versioning and storage

# 2. A small dataset:

data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
recommendations_path = os.path.join(data_dir, "recommendations.json")
with open(recommendations_path, "r") as f:
    inputs = json.load(f)
    
data = []
for input in inputs:
    typed_item = {
        "consumption": NutritionalInformation(
            calories=input["consumption"]["calories"],
            conditional_nutrients=input["consumption"]["conditional_nutrients"],
            macronutrients=input["consumption"]["macronutrients"],
            micronutrients=input["consumption"]["micronutrients"]
        ),
        "targets": input["targets"],
        "target_nutrient": input["target_nutrient"],
        "restrictions": input["restrictions"] if input["restrictions"] else [],
        "user_preferences": input["user_preferences"]
    }
    data.append(typed_item)

def recommendation_metric(datapoint, output):
    """
    Evaluates recommendations based on how well they optimize the target nutrient
    while avoiding overshooting other nutrient targets.
    """
    # Get current consumption and targets
    current = datapoint["input"]["consumption"]
    targets = datapoint["input"]["targets"]
    target_nutrient = datapoint["input"]["target_nutrient"]
    
    # Get nutritional info for each recommended meal
    total_additional = None
    for meal in output.content[0].parsed.meals:
        meal_desc = f"{meal.title}: {meal.ingredients}"
        meal_breakdown = natural_language_macros(meal_desc).content[0].parsed
        
        # Convert MealBreakdown to NutritionalInformation
        meal_nutrition = NutritionalInformation(
            calories=meal_breakdown.calories,
            conditional_nutrients=meal_breakdown.conditional_nutrients.dict(),
            macronutrients=meal_breakdown.macronutrients.dict(),
            micronutrients=meal_breakdown.micronutrients.dict()
        )
        
        if total_additional is None:
            total_additional = meal_nutrition
        else:
            total_additional = total_additional + meal_nutrition
    
    # Calculate final totals
    final_totals = current + total_additional
    
    # Calculate score components
    # 1. How close we get to target nutrient (0 to 1, 1 being perfect)
    target_score = 1.0 - abs(
        getattr(final_totals, target_nutrient) - getattr(targets, target_nutrient)
    ) / getattr(targets, target_nutrient)
    
    # 2. Penalty for overshooting other nutrients (-1 to 0, 0 being perfect)
    penalty = 0
    nutrients_to_check = [
        "calories", "protein", 
        ("macronutrients", "carbohydrates", "total"),
        ("macronutrients", "fat", "total")
    ]
    
    for nutrient in nutrients_to_check:
        if isinstance(nutrient, tuple):
            final_val = final_totals
            target_val = targets
            for attr in nutrient:
                final_val = getattr(final_val, attr)
                target_val = getattr(target_val, attr)
        else:
            final_val = getattr(final_totals, nutrient)
            target_val = getattr(targets, nutrient)
            
        if final_val > target_val:
            penalty += (final_val - target_val) / target_val
            
    penalty = -min(penalty, 1.0)  # Cap penalty at -1
    
    # Combine scores (weighted average favoring target optimization)
    final_score = (0.7 * target_score) + (0.3 * (1 + penalty))
    return final_score

dataset = [
    {"input": data[0]}
]

# 4. Constructing the eval:
eval = ell.evaluation.Evaluation(
    name="recommendation_eval",
    dataset=dataset,
    metrics={"recommendation_score": recommendation_metric}
)

# Run the eval:
result = eval.run(make_recommendations)
print("Average recommendation score:", result.results.metrics["recommendation_score"].mean())