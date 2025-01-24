import json
import os
from typing import Any, Dict, Tuple

import ell
from pydantic import BaseModel, Field

from fit.nutrition.assistants import (natural_language_nutritional_breakdown)
from fit.nutrition.data_models import (MealRecommendation,
                                       NutritionalInformation)

ell.init(store="./logdir") 

MACRONUTRIENTS = ["protein", "carbohydrates", "fat"]
MICRONUTRIENTS = ["vitamin_a", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium", "sodium"]
DEFAULT_MODEL = "gpt-4o-mini-2024-07-18" # TODO: change to a cheaper model 

class MealSemanticSimilarity(BaseModel):
    """A dataclass that contains the semantic similarity for a meal."""
    similarity: float = Field(description="the semantic similarity of the meal to the user's preferences")

def prepare_eval_data():
    """
    Define what the data 
    
    """
    return data



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