"""
Eval for LMPs making meal recommendations based on user preferences and nutritional targets.
"""

import json
import logging
import os
from typing import Any, Dict, Tuple

import ell
import numpy as np
from pydantic import BaseModel, Field

from fit.ai.nutrition.assistants import (
    make_recommendations,
    natural_language_nutritional_breakdown,
)
from fit.ai.nutrition.data_models import MealRecommendation, NutritionalInformation

ell.init(store="./logdir")

MACRONUTRIENTS = ["protein", "carbohydrates", "fat"]
MICRONUTRIENTS = [
    "vitamin_a",
    "vitamin_c",
    "vitamin_d",
    "calcium",
    "iron",
    "potassium",
    "sodium",
]
DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"


class MealSemanticSimilarity(BaseModel):
    """A dataclass that contains the semantic similarity for a meal."""

    similarity: float = Field(
        description="the semantic similarity of the meal to the user's preferences"
    )


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
                micronutrients=input["consumption"]["micronutrients"],
            ),
            "targets": input["targets"],
            "target_nutrient": input["target_nutrient"],
            "restrictions": input["restrictions"] if input["restrictions"] else [],
            "user_preferences": input["user_preferences"],
        }
        data.append(typed_item)
    return data


def semantic_similarity_metric(
    datapoint: Dict[str, Any], output: MealRecommendation
) -> float:
    """Calculate semantic similarity score for non-explorative recommendations."""
    user_preferences = datapoint["input"]["user_preferences"]
    returned_recommendations = output.content[0].parsed.meals
    similarities = []
    for meal in returned_recommendations:
        if not meal.is_explorative:
            similarity = semantic_similarity(meal, user_preferences)
            similarities.append(similarity.content[0].parsed.similarity)

    return sum(similarities) / len(similarities)


def target_nutrient_accuracy_metric(
    datapoint: Dict[str, Any], output: MealRecommendation
) -> float:
    """
    Evaluates recommendations based on how well they optimize the target nutrient.
    """
    current = datapoint["input"]["consumption"]
    targets = datapoint["input"]["targets"]
    target_nutrient = datapoint["input"]["target_nutrient"]

    recommendation_averages, _ = calculate_recommendation_averages(output)
    final_totals = calculate_final_totals(current, recommendation_averages)
    target_score = calculate_target_score(
        final_totals, target_nutrient, targets[target_nutrient]
    )
    return target_score


def non_target_nutrient_accuracy_metric(
    datapoint: Dict[str, Any], output: MealRecommendation
) -> float:
    current = datapoint["input"]["consumption"]
    targets = datapoint["input"]["targets"]
    recommendation_averages, _ = calculate_recommendation_averages(output)
    final_totals = calculate_final_totals(current, recommendation_averages)

    all_nutrients = MACRONUTRIENTS + MICRONUTRIENTS
    final_vals = np.array([final_totals[nutrient] for nutrient in all_nutrients])
    target_vals = np.array([targets[nutrient] for nutrient in all_nutrients])
    target_vals = np.where(target_vals == 0, 1e-10, target_vals)
    scores = np.abs(final_vals - target_vals) / target_vals

    return float(np.mean(scores))


def calculate_recommendation_averages(
    output: MealRecommendation,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, str]]]:
    """Calculate average nutritional values across recommended meals."""
    recommendation_averages = {
        nutrient: 0 for nutrient in MACRONUTRIENTS + MICRONUTRIENTS
    }
    recommendation_averages["calories"] = 0
    recommendation_info = {}

    num_meals = len(output.content[0].parsed.meals)

    for meal in output.content[0].parsed.meals:
        meal_desc = f"{meal.title}: {meal.ingredients}"
        meal_breakdown = (
            natural_language_nutritional_breakdown(meal_desc).content[0].parsed
        )
        recommendation_info[meal_breakdown.title] = {}
        recommendation_averages["calories"] += meal_breakdown.calories

        for nutrient in MACRONUTRIENTS:
            nutrient_value = getattr(meal_breakdown.macronutrients, nutrient)
            if isinstance(nutrient_value, float):
                recommendation_averages[nutrient] += nutrient_value
                recommendation_info[meal_breakdown.title][
                    nutrient
                ] = f"{nutrient_value}g"
            else:
                recommendation_averages[nutrient] += nutrient_value.total
                recommendation_info[meal_breakdown.title][
                    nutrient
                ] = f"{nutrient_value.total}g"

        for nutrient in MICRONUTRIENTS:
            recommendation_averages[nutrient] += getattr(
                meal_breakdown.micronutrients, nutrient
            )
            recommendation_info[meal_breakdown.title][
                nutrient
            ] = f"{getattr(meal_breakdown.micronutrients, nutrient)}g"

    for nutrient in recommendation_averages:
        recommendation_averages[nutrient] /= num_meals

    return recommendation_averages, recommendation_info


def calculate_final_totals(
    current: NutritionalInformation, recommended: Dict[str, float]
) -> Dict[str, float]:
    """Calculate final nutrient totals combining current and recommended values."""
    final_totals = {}
    for nutrient in MACRONUTRIENTS:
        nutrient_value = getattr(current.macronutrients, nutrient)
        if isinstance(nutrient_value, float):
            final_totals[nutrient] = recommended[nutrient] + nutrient_value
        else:
            final_totals[nutrient] = recommended[nutrient] + nutrient_value.total

    for nutrient in MICRONUTRIENTS:
        final_totals[nutrient] = recommended[nutrient] + getattr(
            current.micronutrients, nutrient
        )

    final_totals["calories"] = recommended["calories"] + current.calories
    return final_totals


def calculate_target_score(
    final_totals: Dict[str, float], target_nutrient: str, target_value: float
) -> float:
    """Calculate how close we get to target nutrient (0 to 1, 1 being perfect)."""
    return 1.0 - abs(final_totals[target_nutrient] - target_value) / target_value


@ell.complex(model=DEFAULT_MODEL, response_format=MealSemanticSimilarity)
def semantic_similarity(meal: MealRecommendation, user_preferences: str):
    """Given a meal that is recommended by our recommendation system
    and the user's preferences, calculate a similarity score between that
    and the user's preferences on a 0 to 1 scale. if the meal sounds
    like a perfect match for our user, give it 1, if it is completely
    out of distribution, give it a 0
    """  # TODO: the construction of this eval metric is subjective, edit prompt to make
    # it more consistent
    user_str = f"Meal title: {meal.title}, meal ingredients: {meal.ingredients}"
    user_str = f"{user_str} User preferences: {user_preferences}"
    return user_str


if __name__ == "__main__":
    data = prepare_eval_data()

    dataset = [{"input": data_point} for data_point in data]

    eval = ell.evaluation.Evaluation(
        name="recommendation_eval",
        dataset=dataset,
        metrics={
            "target_nutrient_accuracy": target_nutrient_accuracy_metric,
            "non_target_nutrient_accuracy": non_target_nutrient_accuracy_metric,
            "semantic_similarity_score": semantic_similarity_metric,
        },
    )

    result = eval.run(make_recommendations)

    logging.info(
        "Average target nutrient accuracy:",
        result.results.metrics["target_nutrient_accuracy"].mean(),
    )
    logging.info(
        "Average non-target nutrient accuracy:",
        result.results.metrics["non_target_nutrient_accuracy"].mean(),
    )
    logging.info(
        "Average semantic similarity score:",
        result.results.metrics["semantic_similarity_score"].mean(),
    )
