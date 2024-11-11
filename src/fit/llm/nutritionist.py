import ell 
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

@dataclass
class NutritionalInfo(BaseModel):
    """A dataclass that contains the macro nutrients in grams for a food."""
    protein: float = Field(description="the amount of protein in grams")    
    carbs: float = Field(description="the amount of carbs in grams")
    fat: float = Field(description="the amount of fat in grams")
    calories: float = Field(description="the amount of calories in the food")


@dataclass
class MealOptions(BaseModel):
    """A dataclass that contains the macro nutrients in grams for a food."""
    options: List[str] = Field(description="the list of 3 meal options")



class Goals(Enum):
    """An enum that contains the user's macro goals for the day."""
    LOSE_WEIGHT = "lose weight"
    GAIN_MUSCLE = "gain muscle"
    MAINTENANCE = "maintain current weight and composition"


class NutritionTracker:
    """A class that uses LLMs to help with nutrition tracking."""
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model

    def natural_language_macros(self, food: str) -> NutritionalInfo:
        """Returns the macro nutrients in grams and kilocalories for food described in plain text.
        Args:
            food: The food to get the macro nutrients for.
        """
        @ell.complex(model=self.model, response_format=NutritionalInfo)
        def _natural_language_macros(food: str) -> NutritionalInfo:
            """given what the user ate, return the macro nutrients in grams.
            If the user query is not food, return 0 for all macros.
            """
            return food
        
        return _natural_language_macros(food)
    
    
    def image_macros(self, image: str) -> NutritionalInfo:
        """Returns the macro nutrients in grams and kilocalories for food described in an image.
        Args:
            image: The image to get the macro nutrients for.
        """
        @ell.complex(model=self.model, response_format=NutritionalInfo)
        def _image_macros(image: str) -> NutritionalInfo:
            """given an image of what the user ate, return the macro nutrients in grams.
            If the image is not food, return 0 for all macros.
            """
            return image
        
        return _image_macros(image)

class FoodAssistant:
    """A class that uses LLMs recommend foods. Based on the user's caloric burn and macro goals."""
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model
    
    def make_recommendations(
            self, caloric_burn: float, goal: Goals, 
        ) -> MealOptions:
        """Makes recommendations for foods based on the user's caloric burn and macro goals.
        Args:
            caloric_burn: The user's caloric burn for the day.
            goal: The user's weight goals.
        """
        @ell.complex(model=self.model, response_format=MealOptions)
        def _make_recommendations(caloric_burn: float, goal: Goals) -> MealOptions:
            """given the user's caloric burn and weight goals, recommend foods."""
            user_input = f"The user's caloric burn for the day is {caloric_burn} calories. The user's goal is to {goal.value}."
            print(user_input)
            return user_input
        
        return _make_recommendations(caloric_burn, goal)
