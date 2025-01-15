from fit.nutrition.data_models import Goals


def calculate_caloric_target(calories_burned: float, goal: Goals) -> float:
    """
    Calculate daily caloric target based on calories burned and goal.
    Returns a 10% surplus for gaining, maintenance for maintaining, or 10% deficit for losing.
    """
    if goal == Goals.GAIN_MUSCLE:
        return calories_burned * 1.1
    elif goal == Goals.LOSE_WEIGHT:
        return calories_burned * 0.9
    else:
        return calories_burned

def calculate_protein_target(caloric_target: float) -> float:
    """Calculate daily protein target (30% of calories)."""
    protein_calories = caloric_target * 0.3
    return protein_calories / 4

def calculate_fat_target(caloric_target: float) -> float:
    """Calculate daily fat target (30% of calories)."""
    fat_calories = caloric_target * 0.3
    return fat_calories / 9

def calculate_carb_target(caloric_target: float) -> float:
    """Calculate daily carbohydrate target (40% of calories)."""
    carb_calories = caloric_target * 0.4
    return carb_calories / 4

def calculate_macro_targets(calories_burned: float, goal: Goals) -> dict:
    """
    Calculate all nutritional targets based on calories burned and goal.
    
    Args:
        calories_burned: Total daily calories burned
        goal: Goal enum indicating whether to gain, maintain, or lose
        
    Returns:
        dict: Dictionary containing all daily targets:
            - calories, protein, fat, carbohydrates
    """
    caloric_target = calculate_caloric_target(calories_burned, goal)
    
    return {
        "calories": round(caloric_target),
        "protein": round(calculate_protein_target(caloric_target)),
        "fat": round(calculate_fat_target(caloric_target)),
        "carbohydrates": round(calculate_carb_target(caloric_target))
    }


MICRO_GOALS = {
    "male": {
        "vitamin_a": 900,
        "vitamin_c": 90, 
        "vitamin_d": 15,
        "calcium": 1000,
        "iron": 18,
        "potassium": 3400,
        "sodium": 1500
    },
    "female": {
        "vitamin_a": 700,
        "vitamin_c": 75,
        "vitamin_d": 15, 
        "calcium": 1000,
        "iron": 18,
        "potassium": 2600,
        "sodium": 1500
    }
}

def estimate_daily_water_intake(
        user_measurements: dict,
        user_info: dict,
        daily_calories_burned: float
    ) -> float:
    """
    Estimates daily water intake in milliliters (mL).
    
    Args:
        weight_kg (float): Person's weight in kilograms.
        gender (str): "male" or "female".
        daily_calories_burned (float): Estimated total daily calorie burn (TDEE).
        hot_environment (bool): If True, adds an extra ~250-500 mL for heat/humidity.
    
    Returns:
        float: Estimated daily water intake in mL.
    """
    if user_measurements is None or user_info is None:
        return 3000
    
    weight_lbs = user_measurements["weight"]
    gender = user_info["gender"]
    
    weight_kg = weight_lbs * 0.453592
    base_water = weight_kg * 35
    activity_calories = max(0, daily_calories_burned - 2000)
    activity_water = activity_calories * 1
    total_water = base_water + activity_water

    if gender.lower() == "male":
        if total_water < 3700:
            total_water = 3700
    elif gender.lower() == "female":
        if total_water < 2700:
            total_water = 2700

    return total_water
