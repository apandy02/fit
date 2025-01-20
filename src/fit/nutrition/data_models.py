from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class MealType(Enum):
    """An enum that contains the different types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class Goals(Enum):
    """An enum that contains the user's nutrition and fitness goals."""
    LOSE_WEIGHT = "lose weight"
    GAIN_MUSCLE = "gain muscle"
    MAINTAIN = "maintain current weight and composition"


class Carbohydrates(BaseModel):
    """A dataclass that contains the carbohydrates for a food."""
    total: float = Field(description="carbohydrates in grams")
    fiber: float = Field(description="fiber in grams")
    total_sugar: float = Field(description="total sugar in grams")
    added_sugar: float = Field(description="added sugar in grams")


class Fats(BaseModel):
    """A dataclass that contains the fats for a food."""
    total: float = Field(description="fats in grams")
    saturated: float = Field(description="saturated fats in grams")
    trans: float = Field(description="trans fats in grams")


class Macronutrients(BaseModel):
    """A dataclass that contains the macronutrients for a food."""
    protein: float = Field(description="protein in grams")    
    carbohydrates: Carbohydrates = Field(description="carbohydrates in grams")
    fat: Fats = Field(description="fats in grams")


class Micronutrients(BaseModel):
    """A dataclass that contains the micronutrients for a food."""
    vitamin_a: float = Field(description="the amount of vitamin A in IU")
    vitamin_c: float = Field(description="vitamin C in mg")
    vitamin_d: float = Field(description="vitamin D in IU")
    calcium: float = Field(description="calcium in mg")
    iron: float = Field(description="iron in mg")
    potassium: float = Field(description="potassium in mg")
    sodium: float = Field(description="sodium in mg")


class ConditionalNutrients(BaseModel):
    """A dataclass that contains the conditional nutrients for a food."""
    creatine: float = Field(description="the amount of creatine in the food")


class MealBreakdown(BaseModel):
    """A dataclass that contains the nutritional information for a food."""
    title: str = Field(description="a title for the food description")
    ingredients: str = Field(description="predicted ingredients in the food and their amounts")
    calories: float = Field(description="calories")
    macronutrients: Macronutrients = Field(description="macronutrients")
    micronutrients: Micronutrients = Field(description="micronutrients")
    conditional_nutrients: ConditionalNutrients = Field(description="conditional nutrients")


class NutritionFeedback(BaseModel):
    """A dataclass that contains the feedback for the user's nutrition."""
    summary: str = Field(description="a summary of the feedback for the user's nutrition based on the provided information")
    macronutrients: str = Field(description="Specific feedback on the user's diet relative to their macronutrient intake")
    micronutrients: str = Field(description="Specific feedback on the user's diet relative to their micronutrient intake")
    suggestions: str = Field(description="the suggestions for the user's nutrition")


CARB_DEFAULT = Carbohydrates(total=0, fiber=0, total_sugar=0, added_sugar=0)
FAT_DEFAULT = Fats(total=0, saturated=0, trans=0)
MACRO_DEFAULT = Macronutrients(protein=0, carbohydrates=CARB_DEFAULT, fat=FAT_DEFAULT)
MICRO_DEFAULT = Micronutrients(vitamin_a=0, vitamin_c=0, vitamin_d=0, calcium=0, iron=0, potassium=0, sodium=0)
COND_DEFAULT = ConditionalNutrients(creatine=0)

class NutritionalInformation(BaseModel):
    """
    A dataclass that contains the nutritional information for a food.
    This is a separate class so that we don't have the same restrictions to pass nutrition info
    aroung in non-llm use cases.
    """

    calories: float = Field(description="the amount of calories in the food", default=0)
    macronutrients: Macronutrients = Field(description="the macronutrients in the food", default=MACRO_DEFAULT)
    micronutrients: Micronutrients = Field(description="the micronutrients in the food", default=MICRO_DEFAULT)
    conditional_nutrients: ConditionalNutrients = Field(description="the conditional nutrients in the food", default=COND_DEFAULT)

class MealRecommendation(BaseModel):
    """A dataclass that contains the meal recommendation for a food."""
    #TODO: Maybe I want an explanation of why this meal is being recommended?
    title: str = Field(description="a title for the food. this would be the dish's name if it were on a menu")
    ingredients: str = Field(
        description="predicted ingredients and amounts. formatted comma separated, not bullet points"
    )
    is_explorative: bool = Field(
        description="whether the meal is explorative or not. ie, is it a meal that the user would not typically eat"
    )

class Recommendations(BaseModel):
    """A dataclass that contains the meal recommendations for a food."""
    meals: List[MealRecommendation] = Field(description="A list of 5 meals to be recommended to the user")

class MealTypeRecommendations(BaseModel):
    """A dataclass that contains meal recommendations for a specific meal type."""
    meal_type: MealType = Field(description="the type of meal these recommendations are for")
    meals: List[MealRecommendation] = Field(description="list of 5 recommended meals of this type")

KITCHEN_ITEM_CATEGORIES = [
    "Produce",
    "Meats & Fish",
    "Dairy & Eggs",
    "Bread & Grains",
    "Frozen Items",
    "Snacks & Misc"
]

class KitchenItem(BaseModel):
    """A dataclass that contains the kitchen item for a food."""
    name: str = Field(description="the name of the kitchen item")
    quantity: float = Field(description="the quantity of the kitchen item")
    unit: str = Field(description="the unit of the quantity of the kitchen item")
    category: str = Field(
        description=f"the category of the kitchen item, choose from: {KITCHEN_ITEM_CATEGORIES}"
    )

class KitchenInventory(BaseModel):
    """A dataclass that contains the kitchen inventory for a food."""
    items: List[KitchenItem] = Field(description="the items in the kitchen inventory")


class GroceryListItem(BaseModel):
    """A dataclass that contains the grocery item for a food."""
    name: str = Field(description="the name of the kitchen item")
    quantity: float = Field(description="the quantity of the kitchen item")
    unit: str = Field(description="the unit of the quantity of the kitchen item")
    category: str = Field(
        description=f"the category of the kitchen item, choose from: {KITCHEN_ITEM_CATEGORIES}"
    )
    value: str = Field(description="one sentence about why this item is good for the user")

class GroceryList(BaseModel):
    """A dataclass that contains the grocery list for a food."""
    items: List[GroceryListItem] = Field(description="a list of 5 - 15 items on a grocery list recommended to a user")

class NutrientPerformance(BaseModel):
    """A dataclass that contains the user's performance for a nutrient."""
    nutrient: str = Field(description="name of the nutrient")
    average_intake: float = Field(description="average daily intake")
    target: float = Field(description="daily target")
    performance_ratio: float = Field(description="ratio of intake to target")

class UserPerformance(BaseModel):
    """A dataclass that contains the user's overall nutritional performance."""
    period_days: int = Field(description="number of days this performance data covers")
    nutrients: List[NutrientPerformance] = Field(description="performance data for each tracked nutrient")
