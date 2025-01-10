import json
import os
from typing import Any, Dict, Tuple

import ell
from pydantic import BaseModel, Field

from fit.nutrition.assistants import (make_recommendations,
                                      natural_language_macros)
from fit.nutrition.data_models import (MealRecommendation,
                                       NutritionalInformation)

ell.init(store="./logdir") 

MACRONUTRIENTS = ["protein", "carbohydrates", "fat"]
MICRONUTRIENTS = ["vitamin_a", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium", "sodium"]
DEFAULT_MODEL = "gpt-4o-2024-08-06" # TODO: change to a cheaper model 

class MealSemanticSimilarity(BaseModel):
    """A dataclass that contains the semantic similarity for a meal."""
    similarity: float = Field(description="the semantic similarity of the meal to the user's preferences")

def prepare_eval_data():
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
    return data

def calculate_recommendation_averages(output: MealRecommendation) -> Tuple[Dict[str, float], Dict[str, Dict[str, str]]]:
    """Calculate average nutritional values across recommended meals."""
    recommendation_averages = {nutrient: 0 for nutrient in MACRONUTRIENTS + MICRONUTRIENTS}
    recommendation_averages['calories'] = 0
    recommendation_info = {}
    
    num_meals = len(output.content[0].parsed.meals)
    
    for meal in output.content[0].parsed.meals:
        meal_desc = f"{meal.title}: {meal.ingredients}"
        meal_breakdown = natural_language_macros(meal_desc).content[0].parsed
        recommendation_info[meal_breakdown.title] = {}
        recommendation_averages['calories'] += meal_breakdown.calories
        
        for nutrient in MACRONUTRIENTS:
            nutrient_value = getattr(meal_breakdown.macronutrients, nutrient)
            if isinstance(nutrient_value, float):
                recommendation_averages[nutrient] += nutrient_value
                recommendation_info[meal_breakdown.title][nutrient] = f"{nutrient_value}g"
            else:
                recommendation_averages[nutrient] += nutrient_value.total
                recommendation_info[meal_breakdown.title][nutrient] = f"{nutrient_value.total}g"
        
        for nutrient in MICRONUTRIENTS:
            recommendation_averages[nutrient] += getattr(meal_breakdown.micronutrients, nutrient)
            recommendation_info[meal_breakdown.title][nutrient] = f"{getattr(meal_breakdown.micronutrients, nutrient)}g"

    for nutrient in recommendation_averages:
        recommendation_averages[nutrient] /= num_meals
            
    return recommendation_averages, recommendation_info

def calculate_final_totals(current: NutritionalInformation, recommendation_averages: Dict[str, float]) -> Dict[str, float]:
    """Calculate final nutrient totals combining current and recommended values."""
    final_totals = {}
    for nutrient in MACRONUTRIENTS:
        nutrient_value = getattr(current.macronutrients, nutrient)
        if isinstance(nutrient_value, float):
            final_totals[nutrient] = recommendation_averages[nutrient] + nutrient_value
        else:
            final_totals[nutrient] = recommendation_averages[nutrient] + nutrient_value.total
        
    for nutrient in MICRONUTRIENTS:
        final_totals[nutrient] = recommendation_averages[nutrient] + getattr(current.micronutrients, nutrient)
    
    final_totals['calories'] = recommendation_averages['calories'] + current.calories
    return final_totals

def calculate_target_score(final_totals: Dict[str, float], target_nutrient: str, target_value: float) -> float:
    """Calculate how close we get to target nutrient (0 to 1, 1 being perfect)."""
    return 1.0 - abs(final_totals[target_nutrient] - target_value) / target_value

def calculate_penalty(final_totals: Dict[str, float], targets: Dict[str, float]) -> float:
    """Calculate penalty for overshooting other nutrients (-1 to 0, 0 being perfect)."""
    penalty = 0
    for nutrient in MACRONUTRIENTS + MICRONUTRIENTS:
        final_val = final_totals[nutrient]
        target_val = targets[nutrient]
            
        if final_val > target_val:
            penalty += (final_val - target_val) / target_val
            
    return -min(penalty, 1.0)  # Cap penalty at -1

@ell.complex(model=DEFAULT_MODEL, response_format=MealSemanticSimilarity)
def semantic_similarity(meal: MealRecommendation, user_preferences: str):
    """Given a meal that is recommended by our recommendation system
    and the user's preferences, calculate a similarity score between that 
    and the user's preferences on a 0 to 1 scale. if the meal sounds 
    like a perfect match for our user, give it 1, if it is completely 
    out of distribution, give it a 0
    """
    user_str = f"Meal title: {meal.title}, meal ingredients: {meal.ingredients}"
    user_str = f"{user_str} User preferences: {user_preferences}"
    return user_str

def semantic_similarity_metric(datapoint: Dict[str, Any], output: MealRecommendation) -> float:
    """Calculate semantic similarity score for non-explorative recommendations."""
    user_preferences = datapoint["input"]["user_preferences"]
    returned_recommendations = output.content[0].parsed.meals
    similarities = []
    for meal in returned_recommendations:
        if not meal.is_explorative:
            similarity = semantic_similarity(meal, user_preferences)
            similarities.append(similarity.content[0].parsed.similarity)
    
    return sum(similarities) / len(similarities)

def recommendation_metric(datapoint: Dict[str, Any], output: MealRecommendation) -> float:
    """
    Evaluates recommendations based on how well they optimize the target nutrient
    while avoiding overshooting other nutrient targets.
    """
    current = datapoint["input"]["consumption"]
    targets = datapoint["input"]["targets"]
    target_nutrient = datapoint["input"]["target_nutrient"]
    
    recommendation_averages, _ = calculate_recommendation_averages(output)
    final_totals = calculate_final_totals(current, recommendation_averages)
    target_score = calculate_target_score(final_totals, target_nutrient, targets[target_nutrient])
    penalty = calculate_penalty(final_totals, targets)
    
    final_score = (0.7 * target_score) + (0.3 * (1 + penalty))
    return final_score


if __name__ == "__main__":
    data = prepare_eval_data()

    dataset = [{"input": data_point} for data_point in data]

    eval = ell.evaluation.Evaluation(
        name="recommendation_eval",
        dataset=dataset,
        metrics={
            "recommendation_score": recommendation_metric,
            "semantic_similarity_score": semantic_similarity_metric
        }
    )

    result = eval.run(make_recommendations)
    print("Average recommendation score:", result.results.metrics["recommendation_score"].mean())
    print("Average semantic similarity score:", result.results.metrics["semantic_similarity_score"].mean())