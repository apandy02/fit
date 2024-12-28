from enum import Enum

from pydantic import BaseModel, Field


class Goals(Enum):
    """An enum that contains the user's nutrition and fitness goals."""
    LOSE_WEIGHT = "lose weight"
    GAIN_MUSCLE = "gain muscle"
    MAINTAIN = "maintain current weight and composition"


class Macronutrients(BaseModel):
    """A dataclass that contains the macronutrients for a food."""
    protein: float = Field(description="the amount of protein in grams")    
    carbohydrates: float = Field(description="the amount of carbohydrates in grams")
    fat: float = Field(description="the amount of fat in grams")
    fiber: float = Field(description="the amount of fiber in grams")

    
class Micronutrients(BaseModel):
    """A dataclass that contains the micronutrients for a food."""
    vitamin_a: float = Field(description="the amount of vitamin A in IU")
    vitamin_c: float = Field(description="the amount of vitamin C in mg")
    vitamin_d: float = Field(description="the amount of vitamin D in IU")
    calcium: float = Field(description="the amount of calcium in mg")
    iron: float = Field(description="the amount of iron in mg")
    potassium: float = Field(description="the amount of potassium in mg")
    sodium: float = Field(description="the amount of sodium in mg")


class ConditionalNutrients(BaseModel):
    """A dataclass that contains the conditional nutrients for a food."""
    creatine: float = Field(description="the amount of creatine in the food")

class MealBreakdown(BaseModel):
    """A dataclass that contains the nutritional information for a food."""
    summary: str = Field(description="a summary of the food description (no longer than 8 words)")
    ingredients: str = Field(description="predicted ingredients in the food and their amounts")
    calories: float = Field(description="the amount of calories in the food")
    macronutrients: Macronutrients = Field(description="the macronutrients in the food")
    micronutrients: Micronutrients = Field(description="the micronutrients in the food")
    conditional_nutrients: ConditionalNutrients = Field(description="the conditional nutrients in the food")

## TODO: Deprecate / Replace
class NutritionalInformation(BaseModel):
    """
    A dataclass that contains the nutritional information for a food.
    This is a separate class so that we don't have the same restrictions to pass nutrition info
    aroung in non-llm use cases.
    """
    calories: float = Field(description="the amount of calories in the food", default=0)
    protein: float = Field(description="the amount of protein in grams", default=0)    
    carbs: float = Field(description="the amount of carbs in grams", default=0)
    fat: float = Field(description="the amount of fat in grams", default=0)
    fiber: float = Field(description="the amount of fiber in grams", default=0)
    vitamin_a: float = Field(description="the amount of vitamin A in IU", default=0 )
    vitamin_c: float = Field(description="the amount of vitamin C in mg", default=0)
    vitamin_d: float = Field(description="the amount of vitamin D in IU", default=0)
    calcium: float = Field(description="the amount of calcium in mg", default=0)
    iron: float = Field(description="the amount of iron in mg", default=0)
    potassium: float = Field(description="the amount of potassium in mg", default=0)
    sodium: float = Field(description="the amount of sodium in mg", default=0)
    
