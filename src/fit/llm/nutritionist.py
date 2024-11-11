import ell 
from dataclasses import dataclass
from pydantic import BaseModel, Field

ell.init(verbose=True)

@dataclass
class MacroNutrients(BaseModel):
    protein: float = Field(description="the amount of protein in grams")    
    carbs: float = Field(description="the amount of carbs in grams")
    fat: float = Field(description="the amount of fat in grams")

class FoodAssistant:
    def __init__(self, model: str = "gpt-4o-2024-08-06"):
        self.model = model

    def natural_language_macros(self, food: str) -> MacroNutrients:
        @ell.complex(model=self.model, response_format=MacroNutrients)
        def _natural_language_macros(food: str) -> MacroNutrients:
            """given what the user ate, return the macro nutrients in grams.
            If the user query is not food, return 0 for all macros.
            """
            return food
        return _natural_language_macros(food)
    
    
    def image_macros(self, image: str) -> MacroNutrients:
        @ell.complex(model=self.model, response_format=MacroNutrients)
        def _image_macros(image: str) -> MacroNutrients:
            """given an image of what the user ate, return the macro nutrients in grams.
            If the image is not food, return 0 for all macros.
            """
            return image
        return _image_macros(image)