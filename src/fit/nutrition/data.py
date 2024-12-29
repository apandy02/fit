from enum import Enum

from pydantic import BaseModel, Field


class Goals(Enum):
    """An enum that contains the user's nutrition and fitness goals."""
    LOSE_WEIGHT = "lose weight"
    GAIN_MUSCLE = "gain muscle"
    MAINTAIN = "maintain current weight and composition"


class Carbohydrates(BaseModel):
    """A dataclass that contains the carbohydrates for a food."""
    total: float = Field(description="the total amount of carbohydrates in grams")
    fiber: float = Field(description="the amount of fiber in grams")
    total_sugar: float = Field(description="the amount of total sugar in grams")
    added_sugar: float = Field(description="the amount of added sugar in grams")


class Fats(BaseModel):
    """A dataclass that contains the fats for a food."""
    total: float = Field(description="the total amount of fats in grams")
    saturated: float = Field(description="the amount of saturated fats in grams")
    trans: float = Field(description="the amount of trans fats in grams")


class Macronutrients(BaseModel):
    """A dataclass that contains the macronutrients for a food."""
    protein: float = Field(description="the amount of protein in grams")    
    carbohydrates: Carbohydrates = Field(description="the amount of carbohydrates in grams")
    fat: Fats = Field(description="the amount of fat in grams")


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
    title: str = Field(description="a title for the food description")
    ingredients: str = Field(description="predicted ingredients in the food and their amounts")
    calories: float = Field(description="the amount of calories in the food")
    macronutrients: Macronutrients = Field(description="the macronutrients in the food")
    micronutrients: Micronutrients = Field(description="the micronutrients in the food")
    conditional_nutrients: ConditionalNutrients = Field(description="the conditional nutrients in the food")


class NutritionFeedback(BaseModel):
    """A dataclass that contains the feedback for the user's nutrition."""
    summary: str = Field(description="a summary of the feedback for the user's nutrition based on the provided information")
    macronutrients: str = Field(description="Specific feedback on the user's diet relative to their macronutrient intake")
    micronutrients: str = Field(description="Specific feedback on the user's diet relative to their micronutrient intake")
    suggestions: str = Field(description="the suggestions for the user's nutrition")


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
    
