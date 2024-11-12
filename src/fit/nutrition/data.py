from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

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