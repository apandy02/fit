import ell 
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class Goals(Enum):
    """An enum that contains the user's macro goals for the day."""
    LOSE_WEIGHT = "lose weight"
    GAIN_MUSCLE = "gain muscle"
    MAINTENANCE = "maintain current weight and composition"


@dataclass
class NutritionalInfo(BaseModel):
    """A dataclass that contains the macro nutrients in grams for a food."""
    protein: float = Field(description="the amount of protein in grams")    
    carbs: float = Field(description="the amount of carbs in grams")
    fat: float = Field(description="the amount of fat in grams")
    calories: float = Field(description="the amount of calories in the food")



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
        
        message = _natural_language_macros(food)
        return message.content[0].parsed
    
    
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
        
        message = _image_macros(image)
        return message.content[0].parsed


class FoodAssistant:
    """A class that uses LLMs recommend foods. Based on the user's caloric burn and macro goals."""
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        """
        Args:
            model: The LLM to use.
        """
        self.model = model
    
    def make_recommendations(
            self, caloric_burn: float, goal: Goals, prior_intake: NutritionalInfo
        ) -> str:
        """Makes recommendations for foods based on the user's caloric burn and macro goals.
        Args:
            caloric_burn: The user's caloric burn for the day.
            goal: The user's weight goals.
            prior_intake: The user's prior intake for the day.
        """
        @ell.simple(model=self.model)
        def _make_recommendations(
                caloric_burn: float, goal: Goals, prior_intake: NutritionalInfo
            ) -> str:
            """given the user's caloric burn and weight goals, provide the user with 3 meal options.
            Ensure that your response is concise and easy to understand.
            """
            user_input = f"""
            The user's caloric burn for the day is {caloric_burn} calories. 
            The user's goal is to {goal.value}. 
            The user's prior intake for the day is {prior_intake.protein}g protein, 
            {prior_intake.carbs}g carbs, and {prior_intake.fat}g fat.
            """
            return user_input
        
        return _make_recommendations(caloric_burn, goal, prior_intake)
