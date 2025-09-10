from datetime import datetime

from PIL import Image
import base64
import io

from fit.ai.common import natural_language_agent, DEFAULT_LARGE_MODEL, DEFAULT_SMALL_MODEL, STRUCTURED_MODELS

import fit.ai.nutrition.data_models as dm
from fit.ai.nutrition.errors import NoMealsLoggedError
from fit.utils.lmp_utils import retry


async def natural_language_nutritional_breakdown(food: str) -> dm.MealBreakdown:
    system = """
    Given what the user ate, return the macro nutrients in grams.
    If the user query is not food, return 0 for all macros.
    """
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.MealBreakdown)
    res = await agent.run(food)
    return res.output


async def improve_breakdown(breakdown: dm.MealBreakdown, user_feedback: str) -> dm.MealBreakdown:
    system = """
    Given the user's feedback on your prediction of the breakdown of their meal,
    improve the breakdown.
    """
    prompt = f"""
    The user's feedback on your prediction of the breakdown of their meal is: {user_feedback}
    The breakdown of the meal is: {breakdown}
    """
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.MealBreakdown)
    res = await agent.run(prompt)
    return res.output


async def vision_nutritional_breakdown(image: Image.Image, additional_context: str) -> dm.MealBreakdown:
    system = """
    Given an image of what the user ate, return the macro nutrients in grams.
    If the image is not food, return 0 for all macros. The user may or may not
    provide additional context about the food. If they do, use it to improve your
    prediction.
    """
    img_url = _image_to_data_url(image)
    user_input = f"{additional_context}\n\n![meal_image]({img_url})"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.MealBreakdown)
    res = await agent.run(user_input)
    return res.output


async def summarize_user_preferences(meals: list[dm.MealBreakdown]) -> str:
    system = """
    Given a list of meals the user has eaten, analyze their dietary preferences and patterns.
    Focus on:
    - Cuisine preferences
    - Common protein (and other major nutrients) sources
    - Common ingredients or food combinations
    Return plain text.
    """
    agent = natural_language_agent(DEFAULT_SMALL_MODEL, system, str)
    res = await agent.run(f"Here are the meals I have eaten: {meals}")
    return res.output


async def make_recommendations(
        consumption: dm.NutritionalInformation,
        targets: dict[str, float],
        target_nutrient: str,
        user_preferences: str,
        restrictions: list[str],
        kitchen_inventory: list[dict[str, float]]
    ) -> dm.Recommendations:
    system = """
    You will be given the user's consumed nutritional information, their nutritional targets,
    their dietary restrictions, and a specific nutrient they are asking you for food recommendations to improve.

    Return meal recommendations:
    - 3 meals tailored to their preferences/habits
    - Additional exploratory meals to broaden variety
    - Respect dietary restrictions strictly (health/safety)
    - Consider kitchen inventory when possible
    - Be serving-aware (avoid excessive portions)
    - Balance other nutrients to minimize over/under consumption
    """
    user_input = f"""User Preferences: {user_preferences} 
        Consumption: {str(consumption)}
        Targets: {str(targets)} 
        Dietary Restrictions: {restrictions}.
        Kitchen Inventory: {kitchen_inventory}
        They want to improve their {target_nutrient} intake.
        """
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.Recommendations)
    res = await agent.run(user_input)
    return res.output


async def daily_io_analysis(meals: list[dm.MealBreakdown], target: dict[str, float], restrictions: list[str]) -> dm.NutritionFeedback:
    if len(meals) == 0:
        raise NoMealsLoggedError("No meals logged for today, please log your meals and try again.")

    system = """
    Analyze the user's daily nutritional intake versus their targets and provide a detailed assessment.
    Summary:
    - Caloric balance
    - High-level overview of nutrient performance (over/under/around target)
    Per-nutrient:
    - Start with intake vs goal
    - Evaluate each meal’s contribution
    - Flag excessive meals (>100% of macro target in one meal) and suggest alternatives
    - If before ~8PM and calories exceed target, suggest an appropriate workout
    For excess: suggest portion adjustments.
    For under-target: suggest realistic additions based on preferences, patterns, and restrictions.
    Format all fields as plain text paragraphs. Do not use markdown or bullets. Speak directly as their nutritionist.
    """
    current_time = datetime.now().time()

    meals_str_prefix = f"As of {current_time} are the meals the user has logged today:\n"
    targets_str_prefix = "The user's daily targets are:\n"

    meals_str, targets_str = summarize_daily_meals_and_targets(meals, target)
    restrictions_str = f"The user's dietary restrictions are: {restrictions}"
    user_data = meals_str_prefix + meals_str + targets_str_prefix + targets_str + restrictions_str
    if DEFAULT_LARGE_MODEL in STRUCTURED_MODELS:
        return await _daily_io_analysis_pydantic(system, user_data)
    else:
        return dm.NutritionFeedback.model_validate_json(
            await _daily_io_analysis_simple(system, user_data)
        )


async def _daily_io_analysis_simple(system: str, user_data: str, error_context: str | None = None) -> str:
    system += f"You must absolutely respond in this format as a json string with no exceptions: {dm.NutritionFeedback.model_json_schema()}"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, str)
    res = await agent.run(user_data)
    return res.output


async def _daily_io_analysis_pydantic(system: str, user_data: str) -> dm.NutritionFeedback:
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.NutritionFeedback)
    res = await agent.run(user_data)
    return res.output


@retry(dm.NutritionFeedback)
async def daily_io_analysis_simple(sys_message: str, user_data: str) -> str:
    system = sys_message + f"You must absolutely respond in this format as a json string with no exceptions: {dm.NutritionFeedback.model_json_schema()}"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system)
    res = await agent.run(user_data)
    return res.output


async def weekly_io_analysis(
        meals: dict[datetime, list[dm.MealBreakdown]],
        target: list[dict[str, float]],
        restrictions: list[str]
) -> dm.NutritionFeedback:
    if len(meals) == 0:
        return "No meals logged for today, please log your meals and try again."

    system = """ 
    You are a nutritionist providing feedback on a week's nutrition logs.
    Analyze nutritional intake vs targets (macro/micro), meal timing, and portions.

    - Identify positive patterns and areas for improvement.
    - Focus on repeated patterns impacting goals (e.g., frequent fried foods -> fat target overages).
    - Prioritize 2-3 most important changes.
    - Recommend realistic substitutions that fit taste/texture preferences.
    - Respect dietary restrictions strictly.
    - Aim to refine habits rather than overhaul them.

    Write in plain text paragraphs (no bullets/markdown), addressing the user directly.
    """
    user_data = ""
    for i, (day, meals_) in enumerate(meals.items()):
        day_meals_prefix = f"On {day} the user has logged the following meals:\n"
        day_targets_prefix = f"The user's daily targets for {day} are:\n"
        day_meals_str, day_targets_str = summarize_daily_meals_and_targets(meals_, target[i])
        user_data += day_meals_prefix + day_meals_str + day_targets_prefix + day_targets_str

    user_data += f"The user's dietary restrictions are: {restrictions}"
    if DEFAULT_LARGE_MODEL in STRUCTURED_MODELS:
        analysis = await _weekly_io_analysis_pydantic(system, user_data)
    else:
        analysis_text = await _weekly_io_analysis_simple(system, user_data)
        analysis = dm.NutritionFeedback.model_validate_json(analysis_text)

    return analysis


async def _weekly_io_analysis_pydantic(system: str, user_data: str) -> dm.NutritionFeedback:
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.NutritionFeedback)
    res = await agent.run(user_data)
    return res.output


async def _weekly_io_analysis_simple(system: str, user_data: str) -> str:
    system += f"You must absolutely respond in this format with no exceptions. {dm.NutritionFeedback.model_json_schema()}"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system)
    res = await agent.run(user_data)
    return res.output


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
        nutrient: The nutrient being analyzed
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
        analysis = f"in line with your {nutrient} target"
    
    analysis = f"{analysis} on average" if multiple_days else analysis
    
    return f"{prefix} {analysis}"


async def decipher_inventory(inventory_str: str) -> dm.KitchenInventory:
    system = """
    The user will describe their kitchen inventory in natural language.
    Return a structured list of items present in the inventory.
    """
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.KitchenInventory)
    res = await agent.run(inventory_str)
    return res.output


async def inventory_from_image(image: Image.Image, additional_context: str = "") -> dm.KitchenInventory:
    system = """
    Given an image of the user's kitchen, return a list of items present.
    If the image does not contain foods in the kitchen, return an empty list.
    """
    img_url = _image_to_data_url(image)
    user_input = f"{additional_context}\n\n![kitchen_image]({img_url})"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.KitchenInventory)
    res = await agent.run(user_input)
    return res.output


async def generate_grocery_list(
    user_preferences: str,
    current_inventory: dm.KitchenInventory,
    dietary_restrictions: list[str]
) -> dm.GroceryList:
    system = """
    You are a meal planning and nutrition expert. Create a weekly grocery list that optimizes nutrition
    while respecting preferences and current habits. Do not violate dietary restrictions.
    Consider meal types:
    - Breakfast (quick, energizing)
    - Lunch (balanced)
    - Dinner (can be more elaborate but digestible)
    - Snacks (light, nutritious)
    The list should:
    - Use current inventory; only add missing items
    - Identify ingredients reused across meals
    - Prioritize shelf-stable items
    - Include reasonable weekly quantities
    - Organize by category
    Keep changes incremental and achievable; maintain some familiar comfort foods.
    """
    user_input = f"user_preferences: {user_preferences}\ncurrent_inventory: {current_inventory}\ndietary_restrictions: {dietary_restrictions}"
    agent = natural_language_agent(DEFAULT_LARGE_MODEL, system, dm.GroceryList)
    res = await agent.run(user_input)
    return res.output

def _image_to_data_url(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"
