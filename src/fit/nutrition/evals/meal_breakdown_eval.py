import ell
import numpy as np
from fit.nutrition.assistants import natural_language_nutritional_breakdown
from fit.nutrition.data_models import MealBreakdown
from pydantic import BaseModel, Field
import logging

ell.init(store="./logdir")

MACRONUTRIENTS = ["protein", "carbohydrates", "fat"]
MICRONUTRIENTS = ["vitamin_a", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium", "sodium"]
DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"

class MealSemanticSimilarity(BaseModel):
    """A dataclass that contains the semantic similarity for a meal."""
    similarity: float = Field(description="the semantic similarity of the meal to the user's preferences")

def prepare_eval_data():
    """
    Define the data to be evaluated.
    """
    data = []
    return data

def macro_calorie_consistency_metric(prediction: MealBreakdown, reference: MealBreakdown) -> float:
    """
    Checks how closely the predicted macros' total caloric value matches
    the predicted or reference calories. Returns a score between 0 and 1,
    where 1 indicates perfect consistency.
    """
    predicted_cals_from_macros = (
        prediction.protein * 4
        + prediction.carbohydrates * 4
        + prediction.fat * 9
    )
    difference = abs(predicted_cals_from_macros - prediction.calories)
    if prediction.calories == 0:
        return 1.0 if predicted_cals_from_macros == 0 else 0.0 # avoid division by 0

    normalized_diff = difference / (abs(prediction.calories) + 1e-5)
    score = 1.0 - normalized_diff
    return max(0.0, min(score, 1.0))
    

def ingredients_score_metric(prediction: MealBreakdown, reference: MealBreakdown) -> float:
    """
    Compares predicted ingredients vs. reference ingredients, returning
    a precision/recall-based score or another measure of overlap.
    For demonstration, this is a placeholder returning 0.0.
    
    """
    # TODO: figure out if it is feasible to build a dataset with good ingredient info
    return 0.0

def basic_accuracy_metric(prediction: MealBreakdown, reference: MealBreakdown) -> float:
    """
    Checks how close macros/micros are compared to reference using relative error.
    Returns a score between 0 and 1, where 1 means perfect match.
    Score = 1 - |predicted - reference| / reference
    """
    pred = np.array([prediction.calories, prediction.protein, 
                    prediction.carbohydrates, prediction.fat])
    ref = np.array([reference.calories, reference.protein,
                   reference.carbohydrates, reference.fat])
    
    ref = np.where(ref == 0, 1e-10, ref)
    accuracy = 1 - np.abs(pred - ref) / ref
    
    return float(np.mean(accuracy))

if __name__ == "__main__":
    data = prepare_eval_data()

    dataset = [{"input": data_point} for data_point in data]

    eval = ell.evaluation.Evaluation(
        name="meal_breakdown_eval",
        dataset=dataset,
        metrics={
            "macro_calorie_consistency": macro_calorie_consistency_metric,
            "ingredients_score": ingredients_score_metric,
            "basic_accuracy_score": basic_accuracy_metric
        }
    )
    result = eval.run(natural_language_nutritional_breakdown)

    logging.info("Average Macro Calorie Consistency:", result.results.metrics["macro_calorie_consistency"].mean())
    logging.info("Average Ingredients Score:", result.results.metrics["ingredients_score"].mean())
    logging.info("Average Basic Accuracy Score:", result.results.metrics["basic_accuracy_score"].mean())
