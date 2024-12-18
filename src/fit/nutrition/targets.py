from fit.nutrition.data import Goals


def calculate_caloric_target(calories_burned: float, goal: Goals) -> float:
    """
    Calculate daily caloric target based on calories burned and goal.
    Returns a 10% surplus for gaining, maintenance for maintaining, or 10% deficit for losing.
    
    Args:
        calories_burned: Total daily calories burned
        goal: Goal enum indicating whether to gain, maintain, or lose
        
    Returns:
        float: Daily caloric target
    """
    if goal == Goals.GAIN_MUSCLE:
        return calories_burned * 1.1
    elif goal == Goals.LOSE_WEIGHT:
        return calories_burned * 0.9
    else:
        return calories_burned

def calculate_protein_target(caloric_target: float) -> float:
    """
    Calculate daily protein target (30% of calories).
    
    Args:
        caloric_target: Daily caloric target
        
    Returns:
        float: Daily protein target in grams
    """
    protein_calories = caloric_target * 0.3
    return protein_calories / 4

def calculate_fat_target(caloric_target: float) -> float:
    """
    Calculate daily fat target (30% of calories).
    
    Args:
        caloric_target: Daily caloric target
        
    Returns:
        float: Daily fat target in grams
    """
    fat_calories = caloric_target * 0.3
    return fat_calories / 9

def calculate_carb_target(caloric_target: float) -> float:
    """
    Calculate daily carbohydrate target (40% of calories).
    
    Args:
        caloric_target: Daily caloric target
        
    Returns:
        float: Daily carbohydrate target in grams
    """
    carb_calories = caloric_target * 0.4
    return carb_calories / 4

def calculate_all_targets(calories_burned: float, goal: Goals) -> dict:
    """
    Calculate all nutritional targets based on calories burned and goal.
    
    Args:
        calories_burned: Total daily calories burned
        goal: Goal enum indicating whether to gain, maintain, or lose
        
    Returns:
        dict: Dictionary containing all daily targets:
            - calories: Daily caloric target
            - protein: Daily protein target in grams
            - fat: Daily fat target in grams
            - carbs: Daily carbohydrate target in grams
    """
    caloric_target = calculate_caloric_target(calories_burned, goal)
    
    return {
        "calories": round(caloric_target),
        "protein": round(calculate_protein_target(caloric_target)),
        "fat": round(calculate_fat_target(caloric_target)),
        "carbs": round(calculate_carb_target(caloric_target))
    }
