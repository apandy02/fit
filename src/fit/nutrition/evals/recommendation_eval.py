import ell
import os
import json
from fit.nutrition.assistants import make_recommendations, natural_language_macros
from fit.nutrition.data import NutritionalInformation, MealRecommendation, Recommendations
ell.init(store="./logdir")  # Enable versioning and storage

# 2. A small dataset:

MACRONUTRIENTS = ["protein", "carbohydrates", "fat"]
MICRONUTRIENTS = ["vitamin_a", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium", "sodium"]

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
    
    # Calculate average nutritional info across recommended meals
    recommendation_averages = {nutrient: 0 for nutrient in MACRONUTRIENTS + MICRONUTRIENTS}
    recommendation_averages['calories'] = 0
    
    num_meals = len(output.content[0].parsed.meals)
    
    for meal in output.content[0].parsed.meals:
        meal_desc = f"{meal.title}: {meal.ingredients}"
        meal_breakdown = natural_language_macros(meal_desc).content[0].parsed
        recommendation_averages['calories'] += meal_breakdown.calories
        for nutrient in MACRONUTRIENTS:
            nutrient_value = getattr(meal_breakdown.macronutrients, nutrient)
            if isinstance(nutrient_value, float):
                recommendation_averages[nutrient] += nutrient_value
            else: 
                recommendation_averages[nutrient] += nutrient_value.total
        
        for nutrient in MICRONUTRIENTS:
            recommendation_averages[nutrient] += getattr(meal_breakdown.micronutrients, nutrient)
    
    
    # Calculate averages
    final_totals = {}
    for nutrient in MACRONUTRIENTS:
        recommendation_averages[nutrient] /= num_meals
        nutrient_value = getattr(current.macronutrients, nutrient)
        if isinstance(nutrient_value, float):
            final_totals[nutrient] = recommendation_averages[nutrient] + nutrient_value
        else:
            final_totals[nutrient] = recommendation_averages[nutrient] + nutrient_value.total
        
    for nutrient in MICRONUTRIENTS:
        recommendation_averages[nutrient] /= num_meals
        final_totals[nutrient] = recommendation_averages[nutrient] + getattr(current.micronutrients, nutrient)
    
    final_totals['calories'] = recommendation_averages['calories'] + current.calories
    # Calculate score components
    # 1. How close we get to target nutrient (0 to 1, 1 being perfect)
    target_score = 1.0 - abs(
        final_totals[target_nutrient] - targets[target_nutrient]
    ) / targets[target_nutrient]
    
    # 2. Penalty for overshooting other nutrients (-1 to 0, 0 being perfect)
    penalty = 0
    
    for nutrient in MACRONUTRIENTS + MICRONUTRIENTS:
       
        final_val = final_totals[nutrient]
        target_val = targets[nutrient]
            
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