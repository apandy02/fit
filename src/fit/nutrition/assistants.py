import time
from datetime import datetime
from functools import wraps
from typing import Type

import ell
from PIL import Image
from pydantic import BaseModel, ValidationError

import fit.nutrition.data_models as dm
from fit.nutrition.errors import NoMealsLoggedError

STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_MODEL = "gpt-4o-2024-08-06"


def retry(
    model_class: Type[BaseModel],
    retries: int = 3,
    delay: float = 1.0
):
    """
    A decorator that retries the wrapped function up to 'retries' times
    if Pydantic validation of the output fails against 'model_class'.

    :param model_class: The Pydantic model class used to validate the function output.
    :param retries: Maximum number of retries before giving up.
    :param delay: Delay in seconds between retries.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    result = func(*args, **kwargs)
                    model_class.model_validate(result)  # Validate the output
                    return result
                except ValidationError as validation_error:
                    last_exception = validation_error
                    time.sleep(delay)
            # If all retries failed, re-raise the last validation error
            if last_exception is not None:
                raise last_exception
        return wrapper
    return decorator 


@ell.complex(model=DEFAULT_MODEL, response_format=dm.MealBreakdown)
def natural_language_macros(food: str) -> dm.MealBreakdown:
    """given what the user ate, return the macro nutrients in grams.
    If the user query is not food, return 0 for all macros.
    """
    return food

@ell.complex(model=DEFAULT_MODEL, response_format=dm.MealBreakdown)
def improve_breakdown(breakdown: dm.MealBreakdown, user_feedback: str) -> dm.MealBreakdown:
    """
    Given the user's feedback on your prediction of the breakdown of their meal,
    improve the breakdown.
    """
    prompt = f"""
    The user's feedback on your prediction of the breakdown of their meal is: {user_feedback}
    The breakdown of the meal is: {breakdown}
    """
    return prompt

@ell.complex(model=DEFAULT_MODEL, response_format=dm.MealBreakdown)
def image_macros(image: Image.Image, additional_context: str) -> dm.MealBreakdown:
    system_message = """
    given an image of what the user ate, return the macro nutrients in grams.
    If the image is not food, return 0 for all macros. The user may or may not
    provide additional context about the food. If they do, use it to improve your
    prediction.
    """
    return [
        ell.system(system_message),
        ell.user([additional_context, image]),
    ]
        
@ell.complex(model=DEFAULT_MODEL, max_tokens=200)
def summarize_user_preferences(meals: list[dm.MealBreakdown]) -> str:
    """Given a list of meals the user has eaten, analyze their dietary preferences and patterns.
    For example: "The user frequently eats Indian food, and seems to consume chicken as their 
    primary protein. They also seem to like yogurt."

    Focus on identifying:
    - Cuisine preferences
    - Common protein (and other major nutrients) sources (if any)
    - Common ingredients or food combinations
    """
    prompt = f"Here are the meals I have eaten: {meals}"
    return prompt

@ell.complex(model=DEFAULT_MODEL, response_format=dm.Recommendations)
def make_recommendations(
        consumption: dm.NutritionalInformation,
        targets: dict[str, float],
        target_nutrient: str,
        user_preferences: str,
        restrictions: list[str]
    ) -> dm.Recommendations:
    """You will be given the user's consumed nutritional information, their nutritional targets,
    their dietary restrictions, and a specific nutrient they are asking you for food recommendations to 
    improve.

    You will also be given a summary of the user's dietary preferences and patterns. The list of meals
    you return should contain 3 meals that take this information into account. 
    The others should be exploratory in that they attempt to get the user to try new things.

    Considering all the other nutrient info, try and provide the user with suggestions that 
    minimize risk of over/under consumption of other.

    For example, if the user is asking for food recommendations to improve their vitamin_c intake,
    but they already have a high carbohydrate intake, suggest a vitamin_c rich food that is low in 
    carbohydrates.

    Make sure that the suggestions are serving aware. if the user is 30g of protein under their target,
    it does not make sense to suggest a meal with 100g of chicken, this would be excessive.
    """
    user_input = f"""User Preferences: {user_preferences} \n Consumption: {str(consumption)}
    Targets: {str(targets)} \n Dietary Restrictions: {restrictions}
    They want trying to improve their {target_nutrient} intake.
    """
    return user_input

# TODO: cleanup the following two functions using a factory 
def daily_io_analysis(meals: list[dm.MealBreakdown], target: dict[str, float], restrictions: list[str]) -> dm.NutritionFeedback:
    """
    Analyzes the user's daily intake and target and produces an overview with feedback.
    
    Args:
        meals: The user's meals for the day.
        target: The user's target for the day.
    """
    if len(meals) == 0:
        raise NoMealsLoggedError("No meals logged for today, please log your meals and try again.")
    
    sys_message = """
    Analyze the user's daily nutritional intake versus their targets and provide a detailed assessment. 

    In the summary, talk about the caloric balance, and provide a high level overview of the
    user's nutrition (if they are highly lacking (or over) in some of them, point out that they are, and
    if they're doing well in some of them (around their target), point that out as well).

    For each of the nutrient sections, start with an overview comparing total intake to goals.
    Then evaluate each meal. Discuss any meals that contribute to to any excess or are not nutrititious
    enough if a target is underperformed on. flag meals that significantly exceed targets (e.g., >100% of
    a macro target in one meal) as problematic and suggest alternatives. if it is not too late in the day
    (roughly speaking before 8PM) and they have consumed more calories than their calorie target, suggest a
    workout that get them closer to a target range.
    
    For meals contributing to excess but not extreme, recommend portion adjustments.
    For under-target scenarios, suggest realistic additions based on their evident food preferences,
    eating patterns, and strictly following their dietary restrictions.

    Format all fields as plain text paragraphs. You must not use markdown, bullet points, or 
    special formatting, you are speaking to the user directly as their nutritionist.
    """ # TODO: the workout bit needs to be changed & system message can be passed in as an arg
    current_time = datetime.now().time()

    meals_str_prefix = f"As of {current_time} are the meals the user has logged today:\n"
    targets_str_prefix = "The user's daily targets are:\n"
    
    meals_str, targets_str = summarize_daily_meals_and_targets(meals, target)
    restrictions_str = f"The user's dietary restrictions are: {restrictions}"
    user_data = meals_str_prefix + meals_str + targets_str_prefix + targets_str + restrictions_str
    if DEFAULT_MODEL in STRUCTURED_MODELS:
        return _daily_io_analysis_pydantic(sys_message, user_data)
    else:
        return dm.NutritionFeedback.model_validate_json(
            _daily_io_analysis_simple(sys_message, user_data)
        )
    
@ell.simple(model=DEFAULT_MODEL, max_tokens=2048)
def _daily_io_analysis_simple(sys_message: str, user_data: str) -> str:
    sys_message += f"You must absolutely respond in this format as a json string with no exceptions: {dm.NutritionFeedback.model_json_schema()}"
    return [
        ell.system(sys_message),
        ell.user(user_data)
    ]

@ell.complex(model=DEFAULT_MODEL, response_format=dm.NutritionFeedback, max_tokens=2048)
def _daily_io_analysis_pydantic(sys_message: str, user_data: str) -> dm.NutritionFeedback:
    return [
        ell.system(sys_message),
        ell.user(user_data)
    ]

@retry(dm.NutritionFeedback)
@ell.simple(model=DEFAULT_MODEL, max_tokens=2048)
def daily_io_analysis_simple(sys_message: str, user_data: str) -> str:
    sys_message += f"You must absolutely respond in this format as a json string with no exceptions: {dm.NutritionFeedback.model_json_schema()}"
    return [
        ell.system(sys_message),
        ell.user(user_data)
    ]

def weekly_io_analysis(
        meals: dict[datetime, list[dm.MealBreakdown]],
        target: list[dict[str, float]],
        restrictions: list[str]
) -> dm.NutritionFeedback:
    """
    Analyzes the user's weekly intake and target and produces an overview with feedback.

    Args:
        meals: The user's meals for the week, stored per day.
        target: The user's target for the week, stored per day.
    """
    if len(meals) == 0:
        return "No meals logged for today, please log your meals and try again."

    sys_message = """ 
    You are a nutritionist providing feedback on a week's nutrition logs. Analyze the 
    user's nutritional intake versus their targets, including macro and micronutrient balance,
    meal timing, and portion sizes.
    
    Identify both positive patterns and areas for improvement. 
    When discussing concerns, focus on repeated patterns that significantly impact their 
    nutritional goals. For example, if frequent fried food consumption is causing them to 
    exceed fat targets, point this out specifically.

    Prioritize the 2-3 most important changes that would help them reach their goals. When 
    suggesting modifications, recommend realistic substitutions that maintain similar taste and 
    texture profiles. For instance, if they enjoy crunchy snacks but are exceeding sodium targets,
    suggest specific lower-sodium alternatives they might enjoy.

    Provide practical, actionable suggestions that respect their provided dietary restrictions. 
    Consider their current food preferences when making recommendations - the goal is to refine 
    their existing habits rather than completely overhaul their diet.

    Write your response in plain text paragraphs without bullets or special formatting, address 
    the user directly as their nutritionist.
    """ #TODO: this can be passed in as an arg
    user_data = ""
    for i, (day, meals) in enumerate(meals.items()):
        day_meals_prefix = f"On {day} the user has logged the following meals:\n"
        day_targets_prefix = f"The user's daily targets for {day} are:\n"
        day_meals_str, day_targets_str = summarize_daily_meals_and_targets(meals, target[i])
        user_data += day_meals_prefix + day_meals_str + day_targets_prefix + day_targets_str
    
    user_data += f"The user's dietary restrictions are: {restrictions}"
    if DEFAULT_MODEL in STRUCTURED_MODELS:
        analysis = _weekly_io_analysis_pydantic(
            sys_message, user_data
        )
    else:
        analysis = _weekly_io_analysis_simple(sys_message, user_data)
        analysis = dm.NutritionFeedback.model_validate_json(analysis)
    
    return analysis

@ell.complex(model=DEFAULT_MODEL, response_format=dm.NutritionFeedback)
def _weekly_io_analysis_pydantic(
        sys_message: str,
        user_data: str
) -> dm.NutritionFeedback:
    return [
        ell.system(sys_message),
        ell.user(user_data)
    ]
    
@ell.simple(model=DEFAULT_MODEL, max_tokens=2048)
def _weekly_io_analysis_simple(
        sys_message: str,
        user_data: str
) -> str:
    sys_message += f"You must absolutely respond in this format with no exceptions. {dm.NutritionFeedback.model_json_schema()}"
    return [
        ell.system(sys_message),
        ell.user(user_data)
    ]

def summarize_daily_meals_and_targets(meals: list[dict], target: dict[str, float]) -> tuple[str, str]:
    meals_str = ""
    for _, meal_data in enumerate(meals, 1):
        meal = meal_data["meal"]
        meals_str += f"""Meal {meal.title} - {meal.calories} calories, 
            {meal.macronutrients.protein}g protein, {meal.macronutrients.carbohydrates}g carbohydrates, 
            {meal.macronutrients.fat}g fat\n
            Micros: {meal.micronutrients.vitamin_a}IU vit A, {meal.micronutrients.vitamin_c}mg vit C, 
            {meal.micronutrients.iron}mg iron, {meal.micronutrients.calcium}mg calcium, 
            {meal.micronutrients.sodium}mg sodium, {meal.micronutrients.potassium}mg potassium\n
        """
    targets_str = f"""
        Calories: {target["calories"]}, Protein: {target["protein"]}g,
        Carbohydrates: {target["carbohydrates"]}g, Fat: {target["fat"]}g
        Micronutrient targets: Vitamin A: {target["vitamin_a"]}IU, Vitamin C: {target["vitamin_c"]}mg,
        Iron: {target["iron"]}mg, Calcium: {target["calcium"]}mg,
        Sodium: {target["sodium"]}mg, Potassium: {target["potassium"]}mg
    """
    return meals_str, targets_str
    
def nutrient_analysis(
        nutrient: str,
        unit: str,
        intake: float,
        target: float,
        multiple_days: bool = False
    ) -> str:
    """Analyze if user is over/under their target for a specific nutrient.

    Args:
        nutrient: The nutrient being analyzed (e.g. 'vitamin_a', 'vitamin_c', 'iron', 'calcium', 'sodium', 'potassium')
        intake: The user's intake for this nutrient
        target: The target amount for this nutrient
        multiple_days: Whether the data is for multiple days
    Returns:
        A string indicating if user is over/under target and by how much
    """
    nutrient = nutrient.lower()
    difference = intake - target
    nutrient = "caloric" if nutrient == "calories" else nutrient
    nutrient = "carbohydrate" if nutrient == "carbohydrates" else nutrient
    prefix = "You have been" if multiple_days else "You are currently"

    if difference > 0:
        analysis = f"{abs(difference):.1f}{unit} over your {nutrient} target"
    elif difference < 0:
        analysis = f"{abs(difference):.1f}{unit} under your {nutrient} target"
    else:
        analysis = f"in line with your {nutrient} target" # TODO: change this to range based 
    
    analysis = f"{analysis} on average" if multiple_days else analysis
    
    return f"{prefix} {analysis}"


@ell.complex(model=DEFAULT_MODEL, response_format=dm.KitchenInventory)
def decipher_inventory(inventory_str: str) -> dm.KitchenInventory:
    """The user is going to, in natural language, describe their kitchen inventory.
    You are going to take this description and return a list of the items in the inventory.
    """
    return inventory_str

@ell.complex(model=DEFAULT_MODEL, response_format=dm.KitchenInventory)
def inventory_from_image(image: Image.Image, additional_context: str = "") -> dm.KitchenInventory:
    system_message = """
    given an image of what the user's kitchen looks like, return a list of the items in the kitchen.
    If the image does not contain foods the kitchen, return an empty list.
    """
    return [
        ell.system(system_message),
        ell.user([additional_context, image]),
    ]