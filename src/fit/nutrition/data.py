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
    """A dataclass that contains the nutritional information for a food."""
    summary: str = Field(description="a summary of the food description (no longer than 10 words)")
    # Macros
    protein: float = Field(description="the amount of protein in grams")    
    carbs: float = Field(description="the amount of carbs in grams")
    fat: float = Field(description="the amount of fat in grams")
    calories: float = Field(description="the amount of calories in the food")
    fiber: float = Field(description="the amount of fiber in grams")
    # Micros
    vitamin_a: float = Field(description="the amount of vitamin A in IU")
    vitamin_c: float = Field(description="the amount of vitamin C in mg")
    vitamin_d: float = Field(description="the amount of vitamin D in IU")
    calcium: float = Field(description="the amount of calcium in mg")
    iron: float = Field(description="the amount of iron in mg")
    potassium: float = Field(description="the amount of potassium in mg")
    sodium: float = Field(description="the amount of sodium in mg")
    